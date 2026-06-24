"""Setup scoring for the breakout strategy foundation."""

from typing import Literal

from src.core.enums import ScenarioType, Side
from src.core.models import (
    BreakoutScore,
    ContextDriverSignal,
    ContextFilterConfig,
    FeatureVector,
    ScoreConfig,
    SetupConfig,
    TrendFilterConfig,
)
from src.core.schemas import Bar, OrderBookLevel

Eligibility = Literal["normal", "reduced", "blocked"]


class SetupEvaluator:
    """Calculates deterministic breakout setup scores from feature vectors."""

    def __init__(
        self,
        config: ScoreConfig | None = None,
        *,
        setup_config: SetupConfig | None = None,
        trend_config: TrendFilterConfig | None = None,
        context_config: ContextFilterConfig | None = None,
    ) -> None:
        self.config = config or ScoreConfig()
        self.setup_config = setup_config or SetupConfig()
        self.trend_config = trend_config or TrendFilterConfig()
        self.context_config = context_config or ContextFilterConfig()

    def calculate_features(
        self,
        bars: list[Bar],
        *,
        order_book: list[OrderBookLevel] | None = None,
        side: Side = Side.LONG,
    ) -> FeatureVector:
        """Calculate ATR/EMA/ADX and setup features from closed canonical bars."""

        if not bars:
            msg = "at least one closed bar is required"
            raise ValueError(msg)
        ordered = sorted(bars, key=lambda bar: bar["ts"])
        closes = [bar["close"] for bar in ordered]
        volumes = [bar["volume"] for bar in ordered]
        atr = self._atr(ordered, self.setup_config.atr_period)
        consolidation = self._consolidation_range_atr(ordered, atr=atr)
        approach_velocity = self._approach_velocity(ordered, atr=atr)
        activity_ratio = self._activity_ratio(volumes)
        density_available = bool(order_book)
        density_supports_breakout = self._density_supports(order_book or [], side=side)

        return FeatureVector(
            symbol=ordered[-1]["symbol"],
            timestamp=ordered[-1]["ts"],
            atr=atr,
            ema_fast=self._ema(closes, self.trend_config.ema_fast),
            ema_slow=self._ema(closes, self.trend_config.ema_slow),
            adx=self._adx(ordered, self.trend_config.adx_period),
            consolidation_range_atr=consolidation,
            approach_velocity=approach_velocity,
            activity_ratio=activity_ratio,
            density_available=density_available,
            density_supports_breakout=density_supports_breakout if density_available else None,
        )

    def score(
        self,
        features: FeatureVector,
        *,
        side: Side = Side.LONG,
        scenario: ScenarioType = ScenarioType.CONSOLIDATION_BREAKOUT,
        context_drivers: list[ContextDriverSignal] | None = None,
    ) -> BreakoutScore:
        """Calculate weighted 0-100 breakout score."""

        consolidation = self._score_consolidation(features)
        slow_approach = self._score_slow_approach(features)
        trend = self._score_trend(features, side=side)
        activity = self._score_activity(features)
        density = self._score_density(features)
        base_total = consolidation + slow_approach + trend + activity + density
        total, context_reasons, hard_blocked = self._apply_context_filters(
            base_total,
            side=side,
            context_drivers=context_drivers or [],
        )
        eligibility = "blocked" if hard_blocked else self.eligibility(total)
        rejection_reasons = context_reasons
        if eligibility == "blocked" and total < self.config.threshold_reduced:
            rejection_reasons = [*rejection_reasons, "score_too_low"]

        return BreakoutScore(
            symbol=features.symbol,
            side=side,
            scenario=scenario,
            total=total,
            consolidation=consolidation,
            slow_approach=slow_approach,
            trend=trend,
            activity=activity,
            density=density,
            eligibility=eligibility,
            rejection_reasons=rejection_reasons,
        )

    def _apply_context_filters(
        self,
        total: int,
        *,
        side: Side,
        context_drivers: list[ContextDriverSignal],
    ) -> tuple[int, list[str], bool]:
        """Apply deterministic side-aware context penalties and hard blocks."""

        if not self.context_config.enabled or not context_drivers:
            return total, [], False

        opposing = [driver for driver in context_drivers if driver.opposes_side == side]
        if not opposing:
            return total, [], False

        strongest = max(opposing, key=lambda driver: driver.strength)
        driver_reason = strongest.reason or strongest.name
        reason = f"context_driver:{strongest.name}:{driver_reason}"
        if strongest.strength >= self.context_config.hard_block_threshold:
            return total, ["context_filter_blocked", reason], True

        penalty = round(self.context_config.full_strength_penalty * strongest.strength)
        adjusted_total = max(0, total - penalty)
        reasons = ["context_filter_penalty", reason] if penalty > 0 else []
        return adjusted_total, reasons, False

    def eligibility(self, total: int) -> Eligibility:
        """Return baseline eligibility bucket for a score."""

        if total >= self.config.threshold_normal:
            return "normal"
        if total >= self.config.threshold_reduced:
            return "reduced"
        return "blocked"

    def select_scenario(self, matches: set[ScenarioType]) -> ScenarioType | None:
        """Select the primary scenario using the configured deterministic priority."""

        for scenario in (
            ScenarioType.CONSOLIDATION_BREAKOUT,
            ScenarioType.CASCADE_BREAKOUT,
            ScenarioType.LOCAL_EXTREMUM_BREAKOUT,
            ScenarioType.TRENDLINE_BREAKOUT,
            ScenarioType.DENSITY_SUPPORTED_BREAKOUT,
        ):
            if scenario in matches:
                return scenario
        return None

    def _score_consolidation(self, features: FeatureVector) -> int:
        if features.consolidation_range_atr is None:
            return 0
        if features.consolidation_range_atr <= 1.2:
            return self.config.weight_consolidation
        if features.consolidation_range_atr <= 2.0:
            return self.config.weight_consolidation // 2
        return 0

    def _score_slow_approach(self, features: FeatureVector) -> int:
        if features.approach_velocity is None:
            return 0
        if features.approach_velocity <= 0.35:
            return self.config.weight_slow_approach
        if features.approach_velocity <= 0.70:
            return self.config.weight_slow_approach // 2
        return 0

    def _score_trend(self, features: FeatureVector, *, side: Side) -> int:
        if features.ema_fast is None or features.ema_slow is None:
            return 0

        long_ok = features.ema_fast > features.ema_slow
        short_ok = features.ema_fast < features.ema_slow
        side_ok = long_ok if side is Side.LONG else short_ok
        adx_ok = features.adx is None or features.adx >= self.trend_config.adx_threshold
        return self.config.weight_trend if side_ok and adx_ok else 0

    def _score_activity(self, features: FeatureVector) -> int:
        if features.activity_ratio is None:
            return 0
        if features.activity_ratio >= 1.2:
            return self.config.weight_activity
        if features.activity_ratio >= 1.0:
            return self.config.weight_activity // 2
        return 0

    def _score_density(self, features: FeatureVector) -> int:
        if not features.density_available:
            return 0
        return self.config.weight_density if features.density_supports_breakout else 0

    def _atr(self, bars: list[Bar], period: int) -> float:
        ranges: list[float] = []
        previous_close: float | None = None
        for bar in bars[-period:]:
            true_range = bar["high"] - bar["low"]
            if previous_close is not None:
                true_range = max(
                    true_range,
                    abs(bar["high"] - previous_close),
                    abs(bar["low"] - previous_close),
                )
            ranges.append(true_range)
            previous_close = bar["close"]
        return sum(ranges) / len(ranges)

    def _ema(self, closes: list[float], period: int) -> float | None:
        if not closes:
            return None
        smoothing = 2 / (period + 1)
        value = closes[0]
        for close in closes[1:]:
            value = close * smoothing + value * (1 - smoothing)
        return value

    def _adx(self, bars: list[Bar], period: int) -> float | None:
        if len(bars) < 2:
            return None
        directional: list[float] = []
        for previous, current in zip(bars[-period - 1 :], bars[-period:], strict=False):
            up_move = current["high"] - previous["high"]
            down_move = previous["low"] - current["low"]
            movement = abs(up_move - down_move)
            span = max(current["high"] - current["low"], 1e-9)
            directional.append(min(100.0, movement / span * 100.0))
        return sum(directional) / len(directional) if directional else None

    def _consolidation_range_atr(self, bars: list[Bar], *, atr: float) -> float | None:
        if atr <= 0:
            return None
        window = bars[-self.setup_config.consolidation_bars :]
        if len(window) < 2:
            return None
        high = max(bar["high"] for bar in window)
        low = min(bar["low"] for bar in window)
        return (high - low) / atr

    def _approach_velocity(self, bars: list[Bar], *, atr: float) -> float | None:
        if len(bars) < 2 or atr <= 0:
            return None
        window = bars[-self.setup_config.consolidation_bars :]
        if len(window) < 2:
            return None
        return abs(window[-1]["close"] - window[0]["close"]) / atr / (len(window) - 1)

    def _activity_ratio(self, volumes: list[float]) -> float | None:
        if len(volumes) < 2:
            return None
        baseline = volumes[:-1]
        average = sum(baseline) / len(baseline)
        if average <= 0:
            return None
        return volumes[-1] / average

    def _density_supports(self, levels: list[OrderBookLevel], *, side: Side) -> bool | None:
        if not levels:
            return None
        bid_volume = sum(level["volume"] for level in levels if level["side"] == "bid")
        ask_volume = sum(level["volume"] for level in levels if level["side"] == "ask")
        if side is Side.LONG:
            return bid_volume >= ask_volume
        return ask_volume >= bid_volume
