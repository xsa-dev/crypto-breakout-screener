"""Normalization helpers for canonical market data."""

from datetime import UTC, datetime
from typing import Any

from src.core.schemas import Bar, FeedGap, Tick

_TIMEFRAME_SECONDS = {
    "M1": 60,
    "M5": 300,
    "M15": 900,
    "H1": 3600,
    "H4": 14400,
    "D1": 86400,
}


def to_utc(value: datetime | int | float) -> datetime:
    """Normalize provider timestamps to timezone-aware UTC datetimes."""

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    return datetime.fromtimestamp(value, tz=UTC)


class Normalizer:
    """Converts raw provider data into canonical bars/ticks and detects gaps."""

    def normalize_bar(self, raw: dict[str, Any], *, symbol: str, timeframe: str) -> Bar:
        """Normalize a raw OHLCV-like mapping to a canonical bar."""

        timestamp = raw.get("ts", raw.get("time"))
        if timestamp is None:
            msg = "raw bar must contain ts or time"
            raise ValueError(msg)

        return Bar(
            symbol=symbol,
            timeframe=timeframe,
            ts=to_utc(timestamp),
            open=float(raw["open"]),
            high=float(raw["high"]),
            low=float(raw["low"]),
            close=float(raw["close"]),
            volume=float(raw.get("volume", raw.get("tick_volume", 0.0))),
            spread=float(raw["spread"]) if raw.get("spread") is not None else None,
            source=str(raw["source"]) if raw.get("source") is not None else None,
        )

    def normalize_tick(self, raw: dict[str, Any], *, symbol: str) -> Tick:
        """Normalize a raw tick-like mapping to a canonical tick."""

        timestamp = raw.get("ts", raw.get("time"))
        if timestamp is None:
            msg = "raw tick must contain ts or time"
            raise ValueError(msg)

        return Tick(
            symbol=symbol,
            ts=to_utc(timestamp),
            bid=float(raw["bid"]) if raw.get("bid") is not None else None,
            ask=float(raw["ask"]) if raw.get("ask") is not None else None,
            last=float(raw["last"]) if raw.get("last") is not None else None,
            volume=float(raw["volume"]) if raw.get("volume") is not None else None,
            flags=int(raw["flags"]) if raw.get("flags") is not None else None,
            source=str(raw["source"]) if raw.get("source") is not None else None,
        )

    def deduplicate_bars(self, bars: list[Bar]) -> list[Bar]:
        """Return bars ordered by time with duplicates collapsed by symbol/timeframe/timestamp."""

        by_key: dict[tuple[str, str, datetime], Bar] = {}
        for bar in bars:
            by_key[(bar["symbol"], bar["timeframe"], bar["ts"])] = bar
        return sorted(by_key.values(), key=lambda bar: (bar["symbol"], bar["timeframe"], bar["ts"]))

    def deduplicate_ticks(self, ticks: list[Tick]) -> list[Tick]:
        """Return ticks ordered by time with duplicates collapsed by symbol/timestamp."""

        by_key: dict[tuple[str, datetime], Tick] = {}
        for tick in ticks:
            by_key[(tick["symbol"], tick["ts"])] = tick
        return sorted(by_key.values(), key=lambda tick: (tick["symbol"], tick["ts"]))

    def validate_bar_order(self, bars: list[Bar]) -> None:
        """Raise when bars for the same symbol/timeframe are not monotonic by timestamp."""

        previous_by_stream: dict[tuple[str, str], datetime] = {}
        for bar in bars:
            key = (bar["symbol"], bar["timeframe"])
            previous = previous_by_stream.get(key)
            if previous is not None and bar["ts"] < previous:
                msg = f"bars for {key[0]} {key[1]} are out of order at {bar['ts'].isoformat()}"
                raise ValueError(msg)
            previous_by_stream[key] = bar["ts"]

    def detect_bar_gaps(self, bars: list[Bar], *, expected_seconds: int | None = None) -> list[FeedGap]:
        """Detect timestamp gaps in a canonical bar stream."""

        ordered = self.deduplicate_bars(bars)
        if len(ordered) < 2:
            return []

        expected = expected_seconds or _TIMEFRAME_SECONDS.get(ordered[0]["timeframe"])
        if expected is None:
            msg = f"unknown timeframe {ordered[0]['timeframe']!r}; pass expected_seconds"
            raise ValueError(msg)

        gaps: list[FeedGap] = []
        for previous, current in zip(ordered, ordered[1:], strict=False):
            if previous["symbol"] != current["symbol"] or previous["timeframe"] != current["timeframe"]:
                continue
            actual = int((current["ts"] - previous["ts"]).total_seconds())
            if actual > expected:
                gaps.append(
                    FeedGap(
                        symbol=current["symbol"],
                        timeframe=current["timeframe"],
                        previous_ts=previous["ts"],
                        current_ts=current["ts"],
                        expected_seconds=expected,
                        actual_seconds=actual,
                    )
                )
        return gaps
