"""Менеджер сигналов: прослойка между скринером и торговыми инстансами.

По skill `tradebot-architecture` менеджер принимает сигнал, прогоняет через
фильтры (главный рубильник, торговля, blacklist, кулдаун, объём, лимит сделок)
и при успехе запускает изолированный Tradebot на символ отдельной задачей.

Настройки перечитывает из БД раз в SETTINGS_REFRESH_SECONDS и атомарно подменяет
снапшот целиком (skill `graceful-config-reload`).
"""

__all__ = ["SignalManager"]

import asyncio
from typing import TYPE_CHECKING

from loguru import logger

from src.core import exchange_info
from src.core.config import config
from src.core.env import env
from src.core.schemas import Signal
from src.core.utils import TelegramBot, TimeoutTracker
from src.database import Database, SettingsORM

from . import calculator
from .tradebot import Tradebot

if TYPE_CHECKING:
    from unicex.bybit import Client


class SignalManager:
    """Фильтрует сигналы и запускает Tradebot-инстансы."""

    def __init__(self) -> None:
        """Готовит состояние. Биржевой клиент создаётся асинхронно в start()."""
        self._client: "Client | None" = None  # приватный unicex-клиент Bybit, создаётся в start()
        self._telegram = TelegramBot(bot_token=env.tg_bot_token)
        # Кулдаун на вход в сделку по символу (фильтр шага 3 ТЗ).
        self._cooldown: TimeoutTracker[str] = TimeoutTracker()
        # Отдельный кулдаун на сам сигнал: памп длится секундами и скринер шлёт его
        # каждый тик — без этого Telegram спамит одинаковыми сообщениями.
        self._signal_cooldown: TimeoutTracker[str] = TimeoutTracker()

        # Текущий снапшот настроек — атомарно подменяется целиком в refresh.
        self._settings: SettingsORM | None = None

        # Символы с активными сделками (защита от дубля) и их фоновые задачи.
        self._active: set[str] = set()
        self._tasks: set[asyncio.Task] = set()

        self._is_running = False

    @property
    def current_settings(self) -> SettingsORM | None:
        """Текущий снапшот настроек для consumer'а (read-only)."""
        return self._settings

    async def start(self) -> None:
        """Создаёт приватный клиент, читает настройки и чистит висящие ордера."""
        from unicex.bybit import Client

        self._client = await Client.create(
            api_key=env.bybit_api_key,
            api_secret=env.bybit_api_secret,
        )
        self._is_running = True

        # Первый снапшот настроек — до старта скринера, чтобы consumer не простаивал.
        await self._refresh_settings()

        # Страховка на старте: отменяем все висящие лимитки. Позиции не трогаем.
        await self._cancel_all_open_orders()

    async def refresh_settings_loop(self) -> None:
        """Фоновый цикл перечитывания настроек. Ошибка не убивает цикл навсегда."""
        while self._is_running:
            await asyncio.sleep(config.SETTINGS_REFRESH_SECONDS)
            try:
                await self._refresh_settings()
            except Exception as e:
                logger.error(f"Settings reload failed: {e}")

    async def on_signal(self, signal: Signal) -> None:
        """Обрабатывает сигнал: пишет в журнал, прогоняет фильтры, запускает сделку."""
        symbol = signal["symbol"]
        settings = self._settings
        if settings is None:
            return

        # Антиспам: памп длится секундами и скринер шлёт сигнал каждый тик. Обрабатываем
        # один памп по символу лишь раз в cooldown_minutes — иначе Telegram и журнал
        # засыпаются дублями. Блокируем сразу, чтобы следующие тики выходили молча.
        if self._signal_cooldown.is_blocked(symbol):
            return
        self._signal_cooldown.block(symbol, settings.cooldown_minutes * 60)

        logger.info(
            f"Pump signal for {symbol}: price={signal['current_price']} "
            f"change=+{signal['price_change_percent']:.2f}%"
        )

        # Шаг 2 ТЗ: сигнал пишем ВСЕГДА, даже если торговать не будем.
        async with Database.session_context() as db:
            await db.signal_repo.add(
                symbol=symbol,
                price=signal["current_price"],
                price_change_percent=signal["price_change_percent"],
            )
            await db.commit()

        # Сообщение 1 ТЗ: сигнал в Telegram сразу после срабатывания скринера,
        # ещё до фильтров. Если дальше упрёмся в фильтр — это единственное сообщение.
        await self._notify_signal(signal, settings)

        # Шаг 3 ТЗ: фильтры по порядку. Провал → запись rejected с причиной.
        reject_reason = await self._check_filters(signal, settings)
        if reject_reason is not None:
            # enabled=false — осознанная пауза, строку в trades не пишем.
            if reject_reason != "_paused":
                await self._write_reject(symbol, reject_reason)
            return

        # Все фильтры прошли — занимаем слот и запускаем изолированную сделку.
        self._cooldown.block(symbol, settings.cooldown_minutes * 60)
        self._active.add(symbol)
        task = asyncio.create_task(self._run_tradebot(signal, settings))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def shutdown(self) -> None:
        """Дожидается активных сделок и закрывает ресурсы."""
        self._is_running = False
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        await self._telegram.close()
        if self._client is not None:
            await self._client.close_connection()

    # --- Фильтры ---

    async def _check_filters(self, signal: Signal, settings: SettingsORM) -> str | None:
        """Проверяет фильтры по порядку. Возвращает причину отказа или None.

        Особый маркер '_paused' для enabled=false — по нему запись в trades НЕ пишется.
        """
        symbol = signal["symbol"]

        # Главный рубильник.
        if not settings.enabled:
            return "_paused"

        # Торговля выключена (по дефолту off — сначала смотрим сигналы).
        if not settings.trading_enabled:
            return "trading_disabled"

        # Blacklist — сравниваем по базовому активу: BTCUSDT -> BTC.
        base_asset = symbol.removesuffix("USDT")
        if base_asset in settings.parse_blacklist():
            return "blacklist"

        # Кулдаун: недавно уже была сделка по символу.
        if self._cooldown.is_blocked(symbol):
            return "cooldown"

        # Фильтр по 24h-объёму. Если данных по символу ещё нет — не валим (пропускаем).
        if settings.min_daily_volume_usdt is not None:
            volume = signal["quote_volume_24h"]
            if volume is not None and volume < settings.min_daily_volume_usdt:
                return "low_volume"
            if volume is None:
                logger.warning(f"No 24h volume for {symbol}, skipping volume filter")

        # Лимит одновременных сделок = открытые позиции + висящие лимитки (с биржи).
        if await self._concurrent_trades() >= settings.max_concurrent_trades:
            return "concurrent_limit"

        return None

    async def _concurrent_trades(self) -> int:
        """Считает «сделки в работе»: открытые позиции + висящие лимитные ордера.

        Источник правды — биржа. При ошибке запроса возвращаем большое число,
        чтобы не открыть лишнюю сделку (безопаснее пропустить).
        """
        client = self._require_client()
        try:
            positions = await client.position_info(category="linear", settle_coin="USDT")
            open_orders = await client.open_orders(category="linear", settle_coin="USDT")
        except Exception as e:
            logger.error(f"Failed to count concurrent trades: {e}")
            return 10**9

        # Открытые позиции — те, где размер ненулевой.
        positions_count = sum(
            1 for p in positions["result"]["list"] if float(p.get("size", 0)) > 0
        )
        orders_count = len(open_orders["result"]["list"])
        return positions_count + orders_count

    # --- Запуск сделки ---

    async def _run_tradebot(self, signal: Signal, settings: SettingsORM) -> None:
        """Гоняет одну сделку и гарантированно освобождает слот символа."""
        symbol = signal["symbol"]
        try:
            await Tradebot(
                signal=signal,
                settings=settings,
                client=self._require_client(),
                telegram=self._telegram,
            ).process()
        except Exception as e:
            logger.exception(f"Tradebot {symbol} failed: {e}")
        finally:
            self._active.discard(symbol)

    # --- Вспомогательное ---

    def _require_client(self) -> "Client":
        """Возвращает клиент, гарантируя что он создан (вызывается после start())."""
        if self._client is None:
            raise RuntimeError("Bybit client is not initialized — call start() first")
        return self._client

    async def _refresh_settings(self) -> None:
        """Читает настройки из БД и атомарно подменяет снапшот целиком."""
        async with Database.session_context() as db:
            self._settings = await db.settings_repo.get_or_create()

    async def _cancel_all_open_orders(self) -> None:
        """Отменяет все висящие лимитки по фьючерсам (страховка на старте)."""
        try:
            await self._require_client().cancel_all_orders(category="linear", settle_coin="USDT")
            logger.info("Cancelled all hanging limit orders on startup")
        except Exception as e:
            logger.error(f"Failed to cancel hanging orders on startup: {e}")

    async def _write_reject(self, symbol: str, reason: str) -> None:
        """Пишет в trades строку об отказе входа."""
        async with Database.session_context() as db:
            await db.trade_repo.add(symbol=symbol, status="rejected", reject_reason=reason)
            await db.commit()
        logger.info(f"Trade rejected for {symbol}: {reason}")

    async def _notify_signal(self, signal: Signal, settings: SettingsORM) -> None:
        """Сообщение 1: сигнал пампа со ссылками на TradingView и Bybit (skill signal-links).

        Показывает расчётные уровни входа/TP/SL по фибе из текущих настроек, чтобы
        пользователь видел их сразу в сигнале — ещё до фильтров и выставления ордера.
        """
        symbol = signal["symbol"]
        window_min = signal["window_min"]
        current_price = signal["current_price"]

        # Уровни считаем по той же формуле, что и Tradebot, и округляем под фильтры биржи.
        entry = exchange_info.round_price(
            symbol, calculator.fib_price(window_min, current_price, settings.entry_fib_level)
        )
        tp = exchange_info.round_price(
            symbol, calculator.fib_price(window_min, current_price, settings.take_profit_fib)
        )
        sl = exchange_info.round_price(
            symbol, calculator.fib_price(window_min, current_price, settings.stop_loss_fib)
        )

        tv = config.TRADINGVIEW_URL_TEMPLATE.format(symbol=symbol)
        bybit = config.BYBIT_URL_TEMPLATE.format(symbol=symbol)
        text = (
            f"🚀 <b>ПАМП · {symbol}</b>  <code>+{signal['price_change_percent']:.2f}%</code>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💰 Цена: <b>{current_price}</b>\n"
            f"📉 Минимум окна: {window_min}\n"
            f"\n"
            f"🎯 <b>План сделки</b>\n"
            f"┣ 📥 Вход: <b>{entry}</b>  <i>(fib {settings.entry_fib_level})</i>\n"
            f"┣ ✅ TP: <b>{tp}</b>  <i>(fib {settings.take_profit_fib})</i>\n"
            f"┗ 🛑 SL: <b>{sl}</b>  <i>(fib {settings.stop_loss_fib})</i>\n"
            f"\n"
            f"🔗 <a href='{tv}'>TradingView</a> · <a href='{bybit}'>Bybit</a>"
        )
        await self._telegram.send_message(env.tg_chat_id, text)
