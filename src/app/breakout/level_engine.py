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

    def detect_cascade_levels(self, levels: list[Level], *, atr: float) -> list[Level]:
        """Detect compact level sequences that form cascade structures."""

        if atr <= 0:
            msg = "atr must be positive"
            raise ValueError(msg)

        ordered = sorted(levels, key=lambda level: level.price)
        max_gap = self.config.cascade_gap_atr * atr
        cascades: list[Level] = []
        window: list[Level] = []
        for level in ordered:
            if not window or level.price - window[-1].price <= max_gap:
                window.append(level)
            else:
                cascades.extend(self._cascade_from_window(window))
                window = [level]
        cascades.extend(self._cascade_from_window(window))
        return cascades

    def detect_trendline_levels(self, touch_levels: list[Level], *, tolerance_atr: float, atr: float) -> list[Level]:
        """Detect simple auditable trendline levels from at least three aligned touches."""

        if atr <= 0:
            msg = "atr must be positive"
            raise ValueError(msg)
        if len(touch_levels) < 3:
            return []

        ordered = sorted(touch_levels, key=lambda level: level.created_at)
        first, last = ordered[0], ordered[-1]
        span = max((last.created_at - first.created_at).total_seconds(), 1.0)
        slope = (last.price - first.price) / span
        tolerance = tolerance_atr * atr
        aligned: list[Level] = []
        for level in ordered:
            elapsed = (level.created_at - first.created_at).total_seconds()
            expected = first.price + slope * elapsed
            if abs(level.price - expected) <= tolerance:
                aligned.append(level)
        if len(aligned) < 3:
            return []

        source = aligned[-1]
        return [
            Level(
                level_id=_level_id(
                    source.symbol,
                    LevelType.TRENDLINE,
                    source.timeframe.value,
                    source.price,
                    len(aligned),
                ),
                symbol=source.symbol,
                type=LevelType.TRENDLINE,
                price=source.price,
                timeframe=source.timeframe,
                touches=len(aligned),
                created_at=source.created_at,
                source_indexes=[index for level in aligned for index in level.source_indexes],
                metadata={"slope_per_second": slope, "touches": len(aligned)},
            )
        ]

    def validate_min_touches(self, level: Level, touches: int) -> Level | None:
        """Return a level updated with touches when it meets minimum touch rules."""

        if touches < self.config.min_touches:
            return None
        return level.model_copy(update={"touches": touches})

    def validate_level(self, level: Level, bars: list[Bar], *, atr: float) -> Level:
        """Apply reaction and recent-break validity rules to a level."""

        if atr <= 0:
            msg = "atr must be positive"
            raise ValueError(msg)
        lookback = bars[-self.config.recent_break_lookback_bars :]
        if self._recently_broken(level, lookback):
            invalidated_at = lookback[-1]["ts"] if lookback else level.created_at
            return level.model_copy(
                update={"invalidated_at": invalidated_at, "invalidation_reason": "recent_break"}
            )
        if not self._has_reaction(level, bars, atr=atr):
            return level.model_copy(update={"invalidation_reason": "reaction_too_small"})
        return level

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

    def _cascade_from_window(self, window: list[Level]) -> list[Level]:
        if len(window) < self.config.cascade_min_count:
            return []
        source = window[-1]
        return [
            Level(
                level_id=_level_id(
                    source.symbol,
                    LevelType.CASCADE,
                    source.timeframe.value,
                    source.price,
                    len(window),
                ),
                symbol=source.symbol,
                type=LevelType.CASCADE,
                price=source.price,
                timeframe=source.timeframe,
                touches=sum(level.touches for level in window),
                created_at=source.created_at,
                source_indexes=[index for level in window for index in level.source_indexes],
                metadata={"component_count": len(window)},
            )
        ]

    def _recently_broken(self, level: Level, bars: list[Bar]) -> bool:
        tolerance = self.config.touch_tolerance_atr
        if level.type in {LevelType.PIVOT_HIGH, LevelType.DAILY_HIGH, LevelType.ROUND_NUMBER}:
            return any(bar["close"] > level.price + tolerance for bar in bars)
        if level.type in {LevelType.PIVOT_LOW, LevelType.DAILY_LOW}:
            return any(bar["close"] < level.price - tolerance for bar in bars)
        return False

    def _has_reaction(self, level: Level, bars: list[Bar], *, atr: float) -> bool:
        if not bars:
            return False
        threshold = self.config.min_reaction_atr * atr
        for bar in bars:
            if bar["low"] <= level.price <= bar["high"]:
                reaction = max(abs(bar["high"] - level.price), abs(level.price - bar["low"]))
                if reaction >= threshold:
                    return True
        return False
