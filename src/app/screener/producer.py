"""Producer скринера: собирает рыночные данные Bybit и хранит их в памяти.

По skill `screener-architecture` producer — чистый источник состояния: только
собирает данные (WS-сделки + REST 24h-тикеры) и отдаёт их через публичные
геттеры. Никаких побочных эффектов — ни Telegram, ни БД, ни торговой логики.

WS-инфраструктуру (реконнект, ping/pong, healthcheck) берём из unicex
`UniWebsocketManager` — свой Websocket-класс не пишем (skill `websocket-lifecycle`).
"""

__all__ = ["Producer"]

import asyncio
import time
from typing import TYPE_CHECKING

from loguru import logger
from unicex import Exchange, get_uni_client, get_uni_websocket_manager
from unicex.types import TickerDailyDict, TradeDict

if TYPE_CHECKING:
    from unicex._abc import IUniClient

from src.core.config import config

# Сколько секунд истории сделок держим в окне. Берём с запасом над window_seconds
# из настроек — окно может увеличиться на лету, а данные должны уже быть накоплены.
_MAX_WINDOW_SECONDS = 300

# Период обновления 24h-тикеров (объёмы для фильтра min_daily_volume_usdt), секунды.
_TICKER_DAILY_INTERVAL = 5

# Период проверки новых листингов на бирже, секунды.
_NEW_TICKERS_INTERVAL = 600


class Producer:
    """Собирает сделки по фьючерсам Bybit в скользящее окно и 24h-объёмы."""

    def __init__(self) -> None:
        """Готовит контейнеры состояния. Клиент создаётся асинхронно в run()."""
        # Публичный unicex-клиент Bybit. Создаётся в run() через async-фабрику create().
        self._uni_client: "IUniClient | None" = None
        self._ws_manager = get_uni_websocket_manager(Exchange.BYBIT)(logger=logger)

        # Скользящее окно сделок: symbol -> список (timestamp_ms, price).
        self._trades: dict[str, list[tuple[int, float]]] = {}
        # Последняя цена по символу — обновляется на каждой сделке.
        self._last_price: dict[str, float] = {}
        # Снимок 24h-статистики, перезаписывается целиком на каждом REST-тике.
        self._ticker_daily: TickerDailyDict = {}
        # Символы, на которые уже подняты WS-коннекты (для отслеживания новых листингов).
        self._subscribed: set[str] = set()

        self._websockets: list = []
        self._is_running = False

    async def run(self) -> None:
        """Запускает сбор данных: WS-коннекты + фоновые REST-циклы."""
        self._is_running = True

        # Создаём публичный клиент (ключи не нужны — только публичные эндпоинты).
        self._uni_client = await get_uni_client(Exchange.BYBIT).create()

        # Поднимаем WS-коннекты батчами по всем текущим фьючерсным тикерам.
        await self._subscribe_all()

        # Параллельно крутим REST-циклы: 24h-объёмы и мониторинг новых листингов.
        await asyncio.gather(
            self._update_ticker_daily_task(),
            self._monitor_new_tickers_task(),
        )

    def stop(self) -> None:
        """Останавливает фоновые циклы. WS-коннекты гасятся отдельно в shutdown()."""
        self._is_running = False

    async def shutdown(self) -> None:
        """Корректно закрывает все WS-коннекты и HTTP-сессию клиента."""
        self._is_running = False
        for ws in self._websockets:
            try:
                await ws.stop()
            except Exception as e:
                logger.error(f"Error stopping websocket: {e}")
        if self._uni_client is not None:
            await self._uni_client.close_connection()

    def _require_client(self) -> "IUniClient":
        """Возвращает клиент, гарантируя что он создан (вызывается после run())."""
        if self._uni_client is None:
            raise RuntimeError("UniClient is not initialized — call run() first")
        return self._uni_client

    # --- Публичные геттеры (read-only для consumer) ---

    def get_trades(self) -> dict[str, list[tuple[int, float]]]:
        """Возвращает копию окна сделок (верхний уровень), чтобы consumer не словил
        изменение размера словаря во время итерации."""
        return dict(self._trades)

    def get_last_price(self, symbol: str) -> float | None:
        """Возвращает последнюю цену символа или None, если сделок ещё не было."""
        return self._last_price.get(symbol)

    def get_ticker_daily(self) -> TickerDailyDict:
        """Возвращает снимок 24h-статистики по всем тикерам."""
        return self._ticker_daily

    # --- Внутреннее: WS ---

    async def _subscribe_all(self) -> None:
        """Получает список фьючерсных тикеров и поднимает WS-коннекты батчами."""
        batches = await self._require_client().futures_tickers_batched(
            batch_size=config.WS_BATCH_SIZE
        )

        for batch in batches:
            self._start_ws_for_batch(batch)
            self._subscribed.update(batch)
            # Пауза между handshake'ами — биржа ставит rate limit на старт коннектов.
            await asyncio.sleep(0.5)

        logger.info(
            f"Subscribed to {len(self._subscribed)} symbols in {len(batches)} websockets"
        )

    def _start_ws_for_batch(self, symbols: list[str]) -> None:
        """Создаёт WS-коннект на батч символов и запускает его фоновой задачей."""
        ws = self._ws_manager.futures_trades(callback=self._on_trades, symbols=symbols)
        self._websockets.append(ws)
        # start() блокирующий (внутри recv-loop с реконнектом) — гоняем в отдельной задаче.
        asyncio.create_task(ws.start())

    async def _on_trades(self, trade: TradeDict) -> None:
        """Callback WS: складывает одну сделку в окно и обновляет последнюю цену.

        unicex-обёртка разворачивает список сделок и зовёт callback на каждый
        нормализованный TradeDict по отдельности.
        """
        symbol = trade["s"]
        price = trade["p"]

        window = self._trades.setdefault(symbol, [])
        window.append((trade["t"], price))
        self._last_price[symbol] = price

        # Обрезаем хвост старше окна прямо при записи — отдельный cleaner не нужен.
        cutoff_ms = int(time.time() * 1000) - _MAX_WINDOW_SECONDS * 1000
        if window[0][0] < cutoff_ms:
            self._trades[symbol] = [t for t in window if t[0] >= cutoff_ms]

    # --- Внутреннее: REST-циклы ---

    async def _update_ticker_daily_task(self) -> None:
        """Периодически перезагружает 24h-статистику по всем тикерам."""
        while self._is_running:
            try:
                self._ticker_daily = await self._require_client().futures_ticker_24hr()
            except Exception as e:
                logger.error(f"Failed to update ticker daily: {e}")
            await asyncio.sleep(_TICKER_DAILY_INTERVAL)

    async def _monitor_new_tickers_task(self) -> None:
        """Раз в N минут проверяет новые листинги и поднимает на них WS-коннекты."""
        while self._is_running:
            await asyncio.sleep(_NEW_TICKERS_INTERVAL)
            try:
                tickers = await self._require_client().futures_tickers()
                new_symbols = [s for s in tickers if s not in self._subscribed]
                if new_symbols:
                    logger.info(f"Found {len(new_symbols)} new tickers, subscribing")
                    for i in range(0, len(new_symbols), config.WS_BATCH_SIZE):
                        batch = new_symbols[i : i + config.WS_BATCH_SIZE]
                        self._start_ws_for_batch(batch)
                        self._subscribed.update(batch)
                        await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Failed to monitor new tickers: {e}")
