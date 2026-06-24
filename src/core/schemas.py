"""Рыночные DTO, которые ходят между слоями приложения.

По AGENTS.md рыночные данные описываем через TypedDict — они приходят уже
нормализованными (от unicex), валидация не нужна, а TypedDict даёт типизацию
без оверхеда Pydantic.
"""

from datetime import datetime
from typing import NotRequired, TypedDict


class Signal(TypedDict):
    """Сигнал пампа, который скринер передаёт менеджеру сигналов.

    Поля считает consumer на основе скользящего окна цен.
    """

    symbol: str
    """Полный символ Bybit, например BTCUSDT."""

    current_price: float
    """Текущая (последняя) цена в момент срабатывания."""

    window_min: float
    """Минимальная цена за окно window_seconds."""

    price_change_percent: float
    """На сколько процентов текущая цена выше минимума за окно."""

    quote_volume_24h: float | None
    """Объём торгов за 24ч в USDT. None — данных по тикеру ещё нет."""


class Bar(TypedDict):
    """Canonical OHLCV bar used by the breakout foundation."""

    symbol: str
    timeframe: str
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    spread: NotRequired[float | None]
    source: NotRequired[str | None]


class Tick(TypedDict):
    """Canonical tick used for realtime breakout confirmation."""

    symbol: str
    ts: datetime
    bid: float | None
    ask: float | None
    last: float | None
    volume: float | None
    flags: NotRequired[int | None]
    source: NotRequired[str | None]


class OrderBookLevel(TypedDict):
    """Canonical order-book level for optional density scoring."""

    symbol: str
    ts: datetime
    side: str
    price: float
    volume: float
    source: NotRequired[str | None]


class FeedGap(TypedDict):
    """Detected gap in canonical market data."""

    symbol: str
    timeframe: str
    previous_ts: datetime
    current_ts: datetime
    expected_seconds: int
    actual_seconds: int


__all__ = ["Bar", "FeedGap", "OrderBookLevel", "Signal", "Tick"]
