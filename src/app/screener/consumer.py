"""Consumer скринера: раз в секунду читает состояние producer'а и ищет пампы.

По skill `screener-architecture` consumer — чистая обработка: читает данные
через геттеры producer'а, считает метрику (рост от минимума за окно) и при
срабатывании передаёт сигнал в менеджер. Сам в биржу и БД не ходит.

Пороги (window_seconds, pump_threshold_percent) берёт из текущего снапшота
настроек у менеджера — единый источник правды (skill `graceful-config-reload`).
"""

__all__ = ["Consumer"]

import asyncio
import time

from loguru import logger

from src.core.schemas import Signal

from .producer import Producer

# Период тика consumer'а, секунды. Сделки идут плотно — секунды достаточно.
_PARSE_INTERVAL = 1.0


class Consumer:
    """Ищет пампы по скользящему окну цен и шлёт сигналы менеджеру."""

    def __init__(self, producer: Producer, signal_manager) -> None:
        """
        Args:
            producer: источник рыночных данных (DI, не создаётся внутри).
            signal_manager: менеджер сигналов с методом on_signal и снапшотом настроек.
        """
        self._producer = producer
        self._signal_manager = signal_manager
        self._is_running = False

    async def run(self) -> None:
        """Фоновый цикл: тик раз в _PARSE_INTERVAL. Ошибка тика не убивает цикл."""
        self._is_running = True
        while self._is_running:
            try:
                await self._tick()
            except Exception as e:
                logger.exception(f"Error in consumer tick: {e}")
            await asyncio.sleep(_PARSE_INTERVAL)

    def stop(self) -> None:
        """Останавливает цикл."""
        self._is_running = False

    async def _tick(self) -> None:
        """Один проход по всем символам: ищем памп, при срабатывании — сигнал."""
        settings = self._signal_manager.current_settings
        # До первой загрузки настроек тика нет.
        if settings is None:
            return

        # Главный рубильник: на паузе скринер крутится, но сигналы не считаем.
        if not settings.enabled:
            return

        window_seconds = settings.window_seconds
        threshold = settings.pump_threshold_percent
        now_ms = int(time.time() * 1000)
        cutoff_ms = now_ms - window_seconds * 1000

        for symbol, trades in self._producer.get_trades().items():
            signal = self._check_pump(symbol, trades, cutoff_ms, threshold)
            if signal is not None:
                # Менеджер сам фильтрует и решает, торговать ли. Не блокируем тик.
                await self._signal_manager.on_signal(signal)

    def _check_pump(
        self,
        symbol: str,
        trades: list[tuple[int, float]],
        cutoff_ms: int,
        threshold: float,
    ) -> Signal | None:
        """Проверяет, был ли памп по символу за окно.

        Памп = текущая цена выше минимума окна на threshold процентов и более.
        Возвращает Signal либо None, если данных мало или порог не пройден.
        """
        # Берём только сделки внутри окна.
        prices = [price for ts, price in trades if ts >= cutoff_ms]
        if not prices:
            return None

        window_min = min(prices)
        current_price = self._producer.get_last_price(symbol)
        if current_price is None or window_min <= 0:
            return None

        change_percent = (current_price - window_min) / window_min * 100
        if change_percent < threshold:
            return None

        # Объём за 24ч — для фильтра min_daily_volume_usdt в менеджере (поле q = USDT).
        ticker = self._producer.get_ticker_daily().get(symbol)
        quote_volume_24h = ticker["q"] if ticker is not None else None

        return Signal(
            symbol=symbol,
            current_price=current_price,
            window_min=window_min,
            price_change_percent=round(change_percent, 2),
            quote_volume_24h=quote_volume_24h,
        )
