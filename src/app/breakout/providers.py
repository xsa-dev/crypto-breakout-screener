"""Market-data provider interfaces for the breakout foundation."""

from collections.abc import AsyncIterator, Sequence
from datetime import datetime
from typing import Protocol

from src.core.schemas import Bar, OrderBookLevel, Tick


class MarketDataProvider(Protocol):
    """Broker-neutral market data provider contract.

    This is foundation-only: implementations may be historical, in-memory, CSV, or fake providers.
    Live broker/network adapters are explicitly deferred by OpenSpec.
    """

    async def fetch_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> Sequence[Bar]:
        """Fetch historical canonical bars for a time range."""
        ...

    async def fetch_ticks(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> Sequence[Tick]:
        """Fetch historical/recent canonical ticks for a time range."""
        ...

    async def fetch_order_book(self, symbol: str) -> Sequence[OrderBookLevel] | None:
        """Fetch optional order-book snapshot for density scoring."""
        ...

    def stream_ticks(self, symbol: str) -> AsyncIterator[Tick]:
        """Stream canonical ticks for realtime confirmation."""
        ...
