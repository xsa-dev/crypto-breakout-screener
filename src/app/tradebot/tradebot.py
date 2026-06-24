"""Tradebot — изолированный инстанс на одну сделку.

Один объект = одна попытка входа. Стратегия из ТЗ: лимитный BUY на ретрейс
пампа с TP/SL прямо в ордере, ожидание исполнения с TTL. Позицию не ведём —
TP/SL уже на бирже, она закроет сама.

В trades пишется РОВНО одна строка (executed либо rejected) — гарантируется
флагом _logged и единым методом _log_once.
"""

__all__ = ["Tradebot"]

import asyncio
import time

from loguru import logger

from src.core import exchange_info
from src.core.config import config
from src.core.env import env
from src.core.schemas import Signal
from src.database import Database, SettingsORM

from . import calculator


class Tradebot:
    """Проводит одну сделку: расчёт → лимитка с TP/SL → ожидание исполнения."""

    def __init__(self, signal: Signal, settings: SettingsORM, client, telegram) -> None:
        """
        Args:
            signal: сигнал пампа из скринера.
            settings: снапшот настроек на момент запуска сделки.
            client: приватный unicex-клиент Bybit.
            telegram: общий TelegramBot для алертов.
        """
        self._signal = signal
        self._settings = settings
        self._client = client
        self._telegram = telegram
        self._symbol = signal["symbol"]

        # Гарантия «ровно одна запись в trades».
        self._logged = False

    async def process(self) -> None:
        """Полный цикл сделки. Любая ошибка → одна запись rejected/exchange_error.

        Сообщение «сигнал» (шаг 1–2 ТЗ) шлёт менеджер до фильтров — здесь только
        сообщения про ордер и его результат.
        """
        try:
            entry_str, tp, sl, qty = self._calculate()
        except Exception as e:
            logger.exception(f"Calculation failed for {self._symbol}: {e}")
            await self._log_once(status="rejected", reject_reason="exchange_error", error=str(e))
            await self._notify_error(str(e))
            return

        # Шаг 5 ТЗ: лимитный BUY с TP/SL в одном запросе.
        try:
            order_id = await self._place_order(entry_str, tp, sl, qty)
        except Exception as e:
            logger.exception(f"Order placement failed for {self._symbol}: {e}")
            await self._log_once(status="rejected", reject_reason="exchange_error", error=str(e))
            await self._notify_error(str(e))
            return

        # Сообщение 2 (ордер выставлен).
        await self._notify_order_placed(entry_str, tp, sl, qty)

        # Шаг 6 ТЗ: ждём исполнения с TTL. entry — фолбэк-цена, если биржа не вернёт avgPrice.
        await self._wait_fill(order_id, float(entry_str))

    # --- Расчёт ---

    def _calculate(self) -> tuple[str, str, str, str]:
        """Считает и округляет цену входа, TP, SL и объём.

        Returns:
            (entry_str, tp_str, sl_str, qty_str) — цены/объём уже округлены под
            фильтры биржи (str — отправляем в ордер как есть).
        """
        s = self._settings
        window_min = self._signal["window_min"]
        current_price = self._signal["current_price"]

        # Вход, TP и SL — это уровни Фибоначчи на одном размахе пампа
        # (window_min..current_price). Считаем по единой формуле, округляем по tickSize.
        entry_str = exchange_info.round_price(
            self._symbol, calculator.fib_price(window_min, current_price, s.entry_fib_level)
        )
        tp_str = exchange_info.round_price(
            self._symbol, calculator.fib_price(window_min, current_price, s.take_profit_fib)
        )
        sl_str = exchange_info.round_price(
            self._symbol, calculator.fib_price(window_min, current_price, s.stop_loss_fib)
        )

        # Объём из USDT по цене входа, округляем по stepSize.
        entry = float(entry_str)
        qty_str = exchange_info.round_quantity(
            self._symbol, calculator.quantity_from_usdt(s.order_size_usdt, entry)
        )

        return entry_str, tp_str, sl_str, qty_str

    # --- Биржа ---

    async def _place_order(self, price: str, tp: str, sl: str, qty: str) -> str:
        """Ставит лимитный BUY-ордер с TP/SL. Возвращает orderId."""
        result = await self._client.create_order(
            category="linear",
            symbol=self._symbol,
            side="Buy",
            order_type="Limit",
            qty=qty,
            price=price,
            take_profit=tp,
            stop_loss=sl,
            tpsl_mode="Full",
            time_in_force="GTC",
        )
        order_id = result["result"]["orderId"]
        logger.info(
            f"Limit order placed for {self._symbol}: price={price} qty={qty} tp={tp} sl={sl}"
        )
        return order_id

    async def _wait_fill(self, order_id: str, entry: float) -> None:
        """Поллит статус ордера до TTL. Пишет ровно одну строку в trades.

        Три исхода: исполнился (executed), не исполнился (not_filled + отмена),
        ошибка биржи (exchange_error).
        """
        deadline = time.monotonic() + self._settings.order_ttl_seconds

        while time.monotonic() < deadline:
            try:
                order = await self._fetch_order(order_id)
            except Exception as e:
                logger.exception(f"Poll failed for {self._symbol}: {e}")
                await self._log_once(
                    status="rejected", reject_reason="exchange_error", error=str(e)
                )
                await self._notify_error(str(e))
                return

            status = order.get("orderStatus", "")

            # Исполнен (хотя бы частично считаем входом — позиция открыта).
            if status in ("Filled", "PartiallyFilled"):
                avg_price = float(order.get("avgPrice") or entry)
                logger.success(
                    f"Limit order filled for {self._symbol}: entry_price={avg_price}"
                )
                await self._log_once(status="executed", entry_price=avg_price)
                await self._notify_filled(avg_price)
                return

            # Биржа отвергла/отменила ордер сама.
            if status in ("Rejected", "Cancelled", "Deactivated"):
                await self._log_once(
                    status="rejected",
                    reject_reason="exchange_error",
                    error=f"order status={status}",
                )
                await self._notify_error(f"order status={status}")
                return

            await asyncio.sleep(config.ORDER_POLL_INTERVAL)

        # TTL истёк — отменяем висящий ордер и пишем not_filled.
        await self._cancel_order(order_id)
        await self._log_once(status="rejected", reject_reason="not_filled")
        await self._notify_cancelled()

    async def _fetch_order(self, order_id: str) -> dict:
        """Возвращает данные ордера по orderId (realtime open/closed orders)."""
        resp = await self._client.open_orders(
            category="linear", symbol=self._symbol, order_id=order_id
        )
        orders = resp["result"]["list"]
        return orders[0] if orders else {}

    async def _cancel_order(self, order_id: str) -> None:
        """Отменяет ордер. Ошибку игнорируем — он мог уже исполниться."""
        try:
            await self._client.cancel_order(
                category="linear", symbol=self._symbol, order_id=order_id
            )
        except Exception as e:
            logger.debug(f"Cancel order {order_id} for {self._symbol}: {e}")

    # --- Журнал ---

    async def _log_once(
        self,
        status: str,
        entry_price: float | None = None,
        reject_reason: str | None = None,
        error: str | None = None,
    ) -> None:
        """Пишет единственную строку в trades за всю жизнь инстанса."""
        if self._logged:
            return
        self._logged = True

        async with Database.session_context() as db:
            await db.trade_repo.add(
                symbol=self._symbol,
                status=status,
                entry_price=entry_price,
                reject_reason=reject_reason,
                error=error,
            )
            await db.commit()
        logger.info(f"Trade logged for {self._symbol}: status={status} reason={reject_reason}")

    # --- Telegram (skill telegram-alerts + signal-links) ---

    async def _notify_order_placed(self, entry: str, tp: str, sl: str, qty: str) -> None:
        """Сообщение 2: лимитка выставлена (ещё не в позиции)."""
        s = self._settings
        text = (
            f"📥 <b>ЛИМИТКА · {self._symbol}</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"┣ 📥 Вход: <b>{entry}</b>  <i>(fib {s.entry_fib_level})</i>\n"
            f"┣ ✅ TP: <b>{tp}</b>  <i>(fib {s.take_profit_fib})</i>\n"
            f"┣ 🛑 SL: <b>{sl}</b>  <i>(fib {s.stop_loss_fib})</i>\n"
            f"┗ 📦 Объём: <b>{qty}</b>\n"
            f"\n"
            f"⏳ Ждём исполнения до {s.order_ttl_seconds}с"
        )
        await self._telegram.send_message(env.tg_chat_id, text)

    async def _notify_filled(self, avg_price: float) -> None:
        """Сообщение 3 (исполнено): вошли в позицию, TP/SL уже на бирже."""
        bybit = config.BYBIT_URL_TEMPLATE.format(symbol=self._symbol)
        text = (
            f"✅ <b>ИСПОЛНЕН · {self._symbol}</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📥 Цена входа: <b>{avg_price}</b>\n"
            f"🔗 <a href='{bybit}'>Позиция на Bybit</a>"
        )
        await self._telegram.send_message(env.tg_chat_id, text)

    async def _notify_cancelled(self) -> None:
        """Сообщение 3 (отменён): не исполнился за TTL."""
        text = (
            f"🚫 <b>ОТМЕНЁН · {self._symbol}</b>\n"
            f"Лимитка не исполнилась за TTL"
        )
        await self._telegram.send_message(env.tg_chat_id, text)

    async def _notify_error(self, error: str) -> None:
        """Сообщение 3 (ошибка): биржа отвергла ордер."""
        text = (
            f"❗️ <b>ОШИБКА · {self._symbol}</b>\n"
            f"{error}"
        )
        await self._telegram.send_message(env.tg_chat_id, text)
