"""Setup scoring for the breakout strategy foundation."""

import statistics
from typing import Literal, cast

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


def _score_component_value(value: float | None) -> float | str:
    return value if value is not None else "unavailable"


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
        level_price: float | None = None,
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
        proxy = self._ohlcv_density_proxy(
            ordered,
            atr=atr,
            level_price=level_price if level_price is not None else ordered[-1]["close"],
            side=side,
        )
        calibration_blockers = self._calibration_blockers(ordered)

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
            density_source="dom"
            if density_available
            else cast(Literal["ohlcv_proxy", "unavailable"], proxy["density_source"]),
            volume_near_level=cast(float | None, proxy["volume_near_level"]),
            relative_volume_expansion=cast(float | None, proxy["relative_volume_expansion"]),
            body_dominance=cast(float | None, proxy["body_dominance"]),
            wick_rejection=cast(float | None, proxy["wick_rejection"]),
            close_location_quality=cast(float | None, proxy["close_location_quality"]),
            absorption_or_hold_proxy=cast(float | None, proxy["absorption_or_hold_proxy"]),
            normalized_threshold_mode=self.setup_config.normalization_mode,
            calibration_artifact_path=self.setup_config.calibration_artifact_path,
            calibration_window_start=self.setup_config.calibration_window_start,
            calibration_window_end=self.setup_config.calibration_window_end,
            missing_feature_blockers=[
                *cast(list[str], proxy["missing_feature_blockers"]),
                *calibration_blockers,
            ],
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
        if features.missing_feature_blockers:
            eligibility = "blocked"
            rejection_reasons = [*rejection_reasons, *features.missing_feature_blockers]
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
            density_source=features.density_source,
            density_proxy_components={
                "volume_near_level": _score_component_value(features.volume_near_level),
                "relative_volume_expansion": _score_component_value(features.relative_volume_expansion),
                "body_dominance": _score_component_value(features.body_dominance),
                "wick_rejection": _score_component_value(features.wick_rejection),
                "close_location_quality": _score_component_value(features.close_location_quality),
                "absorption_or_hold_proxy": _score_component_value(features.absorption_or_hold_proxy),
            },
            normalized_threshold_mode=features.normalized_threshold_mode,
            calibration_artifact_path=features.calibration_artifact_path,
            missing_feature_blockers=list(features.missing_feature_blockers),
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
        if features.density_source == "dom" or (
            features.density_available and features.density_source == "unavailable"
        ):
            return self.config.weight_density if features.density_supports_breakout else 0
        proxy_values = [
            features.volume_near_level,
            features.relative_volume_expansion,
            features.body_dominance,
            features.wick_rejection,
            features.close_location_quality,
            features.absorption_or_hold_proxy,
        ]
        if features.density_source != "ohlcv_proxy" or any(value is None for value in proxy_values):
            return 0
        normalized_relative_volume = min(float(features.relative_volume_expansion or 0.0) / 1.5, 1.0)
        normalized_volume_near_level = min(float(features.volume_near_level or 0.0), 1.0)
        average = statistics.fmean(
            [
                normalized_volume_near_level,
                normalized_relative_volume,
                float(features.body_dominance or 0.0),
                float(features.wick_rejection or 0.0),
                float(features.close_location_quality or 0.0),
                float(features.absorption_or_hold_proxy or 0.0),
            ]
        )
        return round(self.config.weight_density * average)

    def _ohlcv_density_proxy(
        self,
        bars: list[Bar],
        *,
        atr: float,
        level_price: float,
        side: Side,
    ) -> dict[str, object]:
        missing: list[str] = []
        if atr <= 0:
            return self._missing_density_proxy("missing_density_proxy_atr")
        lookback = self.setup_config.density_proxy_lookback_bars
        window = bars[-lookback:]
        if len(window) < 3:
            return self._missing_density_proxy("missing_density_proxy_history")
        tolerance = self.setup_config.density_level_tolerance_atr * atr
        near_level = [
            bar
            for bar in window
            if bar["low"] - tolerance <= level_price <= bar["high"] + tolerance
        ]
        total_volume = sum(max(0.0, bar["volume"]) for bar in window)
        if total_volume <= 0:
            return self._missing_density_proxy("missing_density_proxy_volume")
        current = bars[-1]
        current_range = current["high"] - current["low"]
        if current_range <= 0:
            return self._missing_density_proxy("missing_density_proxy_candle_range")
        baseline_volumes = [bar["volume"] for bar in window[:-1] if bar["volume"] > 0]
        if not baseline_volumes:
            missing.append("missing_density_proxy_volume_baseline")
        baseline_volume = statistics.median(baseline_volumes) if baseline_volumes else 0.0
        body = abs(current["close"] - current["open"])
        upper_wick = current["high"] - max(current["open"], current["close"])
        lower_wick = min(current["open"], current["close"]) - current["low"]
        adverse_wick = lower_wick if side is Side.LONG else upper_wick
        close_location = (current["close"] - current["low"]) / current_range
        if side is Side.SHORT:
            close_location = (current["high"] - current["close"]) / current_range
        hold_score = self._absorption_or_hold_proxy(window, level_price=level_price, tolerance=tolerance, side=side)
        return {
            "density_source": "ohlcv_proxy" if not missing else "unavailable",
            "volume_near_level": sum(max(0.0, bar["volume"]) for bar in near_level) / total_volume,
            "relative_volume_expansion": current["volume"] / baseline_volume if baseline_volume > 0 else None,
            "body_dominance": min(max(body / current_range, 0.0), 1.0),
            "wick_rejection": min(max(1.0 - max(0.0, adverse_wick) / current_range, 0.0), 1.0),
            "close_location_quality": min(max(close_location, 0.0), 1.0),
            "absorption_or_hold_proxy": hold_score,
            "missing_feature_blockers": missing,
        }

    def _missing_density_proxy(self, reason: str) -> dict[str, object]:
        return {
            "density_source": "unavailable",
            "volume_near_level": None,
            "relative_volume_expansion": None,
            "body_dominance": None,
            "wick_rejection": None,
            "close_location_quality": None,
            "absorption_or_hold_proxy": None,
            "missing_feature_blockers": [reason],
        }

    def _absorption_or_hold_proxy(
        self,
        bars: list[Bar],
        *,
        level_price: float,
        tolerance: float,
        side: Side,
    ) -> float:
        tests = [bar for bar in bars if bar["low"] - tolerance <= level_price <= bar["high"] + tolerance]
        if not tests:
            return 0.0
        holds = 0
        for bar in tests:
            if side is Side.LONG and bar["close"] >= level_price - tolerance:
                holds += 1
            if side is Side.SHORT and bar["close"] <= level_price + tolerance:
                holds += 1
        return min(holds / max(3, len(tests)), 1.0)

    def _calibration_blockers(self, bars: list[Bar]) -> list[str]:
        if self.setup_config.normalization_mode != "calibration_artifact":
            return []
        if self.setup_config.calibration_window_end is None:
            return ["missing_calibration_window_end"]
        if bars[-1]["ts"] <= self.setup_config.calibration_window_end:
            return ["calibration_window_not_closed_before_candidate"]
        return []

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
