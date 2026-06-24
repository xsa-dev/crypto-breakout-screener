"""Foundation level detection for the breakout strategy."""

from datetime import UTC, datetime
from hashlib import sha1

from src.core.enums import LevelType, TimeFrame
from src.core.models import Level, LevelDetectionConfig
from src.core.schemas import Bar


def _level_id(symbol: str, level_type: LevelType, timeframe: str, price: float, index: int) -> str:
    raw = f"{symbol}:{level_type.value}:{timeframe}:{price:.12f}:{index}".encode()
    return sha1(raw, usedforsecurity=False).hexdigest()[:16]


class LevelEngine:
    """Detects auditable levels using closed-bar-only rules."""

    def __init__(self, config: LevelDetectionConfig | None = None) -> None:
        self.config = config or LevelDetectionConfig()

    def detect_pivots(self, bars: list[Bar], *, as_of_index: int | None = None) -> list[Level]:
        """Detect confirmed pivot highs/lows without look-ahead leakage.

        `as_of_index` is the last bar index available to the online strategy. A pivot at `i` is
        eligible only when `i + pivot_right_bars <= as_of_index`.
        """

        if not bars:
            return []

        last_index = len(bars) - 1 if as_of_index is None else min(as_of_index, len(bars) - 1)
        left = self.config.pivot_left_bars
        right = self.config.pivot_right_bars
        levels: list[Level] = []

        for index in range(left, last_index + 1):
            if index + right > last_index:
                continue

            candidate = bars[index]
            left_bars = bars[index - left : index]
            right_bars = bars[index + 1 : index + right + 1]

            if all(candidate["high"] > bar["high"] for bar in [*left_bars, *right_bars]):
                levels.append(self._make_level(candidate, LevelType.PIVOT_HIGH, candidate["high"], index))

            if all(candidate["low"] < bar["low"] for bar in [*left_bars, *right_bars]):
                levels.append(self._make_level(candidate, LevelType.PIVOT_LOW, candidate["low"], index))

        return levels

    def detect_round_levels(self, bars: list[Bar], *, round_step: float) -> list[Level]:
        """Detect round-number levels touched by bar ranges."""

        if round_step <= 0:
            msg = "round_step must be positive"
            raise ValueError(msg)

        seen: set[float] = set()
        levels: list[Level] = []
        for index, bar in enumerate(bars):
            lower = int(bar["low"] // round_step)
            upper = int(bar["high"] // round_step)
            for multiple in range(lower, upper + 1):
                price = multiple * round_step
                if price in seen:
                    continue
                seen.add(price)
                levels.append(self._make_level(bar, LevelType.ROUND_NUMBER, price, index))
        return levels

    def detect_daily_levels(self, bars: list[Bar]) -> list[Level]:
        """Detect daily high/low levels from D1 bars."""

        levels: list[Level] = []
        for index, bar in enumerate(bars):
            if bar["timeframe"] != TimeFrame.D1.value:
                continue
            levels.append(self._make_level(bar, LevelType.DAILY_HIGH, bar["high"], index))
            levels.append(self._make_level(bar, LevelType.DAILY_LOW, bar["low"], index))
        return levels

    def validate_min_touches(self, level: Level, touches: int) -> Level | None:
        """Return a level updated with touches when it meets minimum touch rules."""

        if touches < self.config.min_touches:
            return None
        return level.model_copy(update={"touches": touches})

    def _make_level(self, bar: Bar, level_type: LevelType, price: float, index: int) -> Level:
        timeframe = TimeFrame(bar["timeframe"])
        created_at = bar["ts"] if isinstance(bar["ts"], datetime) else datetime.now(tz=UTC)
        return Level(
            level_id=_level_id(bar["symbol"], level_type, bar["timeframe"], price, index),
            symbol=bar["symbol"],
            type=level_type,
            price=price,
            timeframe=timeframe,
            touches=1,
            created_at=created_at,
            source_indexes=[index],
        )
