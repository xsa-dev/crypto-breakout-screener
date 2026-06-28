"""Entry-time algorithmic breakout score for portfolio candidate ranking."""

from __future__ import annotations

from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field

AlgorithmicEligibilityBucket = Literal["blocked", "reduced_priority", "normal_priority"]

COMPONENT_WEIGHTS: dict[str, int] = {
    "cost_feasibility": 15,
    "btc_eth_regime": 15,
    "market_breadth": 15,
    "relative_strength": 15,
    "volatility_compression": 15,
    "volume_activity_expansion": 10,
    "atr_breakout_distance": 10,
    "multi_timeframe_trend": 5,
}
FORBIDDEN_INPUT_FIELDS = {
    "realized_pnl",
    "net_pnl",
    "gross_pnl",
    "exit_price",
    "exit_time",
    "future_bars",
    "archived_contribution_rank",
    "source_contribution_rank",
}


class AlgorithmicBreakoutScoreInput(BaseModel):
    """Allowed public entry-time inputs for algorithmic score calculation."""

    model_config = ConfigDict(extra="forbid")

    entry_price: float = Field(gt=0)
    spread: float = Field(default=0.0, ge=0)
    slippage_per_unit: float = Field(default=0.0, ge=0)
    feature_context_H1_trend_alignment: str | None = None
    feature_context_H4_trend_alignment: str | None = None
    feature_context_D1_trend_alignment: str | None = None
    feature_btcusdt_regime_agreement: float | None = Field(default=None, ge=0, le=1)
    feature_ethusdt_regime_agreement: float | None = Field(default=None, ge=0, le=1)
    feature_fixed_universe_positive_symbol_ratio: float | None = Field(default=None, ge=0, le=1)
    feature_fixed_universe_breadth_ratio: float | None = Field(default=None, ge=0, le=1)
    feature_relative_strength_vs_btcusdt: float | None = None
    feature_relative_strength_vs_ethusdt: float | None = None
    feature_recent_range_compression: float | None = Field(default=None, ge=0)
    feature_consolidation_range_atr: float | None = Field(default=None, ge=0)
    feature_volume_ratio: float | None = Field(default=None, ge=0)
    feature_activity_ratio: float | None = Field(default=None, ge=0)
    feature_breakout_distance_atr: float | None = Field(default=None, ge=0)
    feature_ema_slope_atr: float | None = None


class AlgorithmicBreakoutScore(BaseModel):
    """Deterministic 0..100 score and candidate priority bucket."""

    profile: Literal["algorithmic-breakout-score-v1"] = "algorithmic-breakout-score-v1"
    total_score: int = Field(ge=0, le=100)
    component_scores: dict[str, int]
    eligibility_bucket: AlgorithmicEligibilityBucket
    rejection_reasons: list[str] = Field(default_factory=list)
    unavailable_components: list[str] = Field(default_factory=list)


def calculate_algorithmic_breakout_score(
    raw_inputs: dict[str, Any],
) -> AlgorithmicBreakoutScore:
    """Calculate score from explicit entry-time public features only."""

    forbidden = sorted(FORBIDDEN_INPUT_FIELDS.intersection(raw_inputs))
    if forbidden:
        msg = f"algorithmic score forbids outcome/future inputs: {', '.join(forbidden)}"
        raise ValueError(msg)
    inputs = AlgorithmicBreakoutScoreInput.model_validate(raw_inputs)
    unavailable: list[str] = []
    component_scores = {
        "cost_feasibility": _cost_feasibility(inputs),
        "btc_eth_regime": _btc_eth_regime(inputs, unavailable),
        "market_breadth": _market_breadth(inputs, unavailable),
        "relative_strength": _relative_strength(inputs, unavailable),
        "volatility_compression": _volatility_compression(inputs, unavailable),
        "volume_activity_expansion": _volume_activity(inputs, unavailable),
        "atr_breakout_distance": _atr_breakout_distance(inputs, unavailable),
        "multi_timeframe_trend": _multi_timeframe_trend(inputs, unavailable),
    }
    total = min(100, max(0, sum(component_scores.values())))
    if total < 70:
        bucket: AlgorithmicEligibilityBucket = "blocked"
        reasons = ["portfolio_selection_algorithmic_score_below_threshold"]
    elif total < 85:
        bucket = "reduced_priority"
        reasons = []
    else:
        bucket = "normal_priority"
        reasons = []
    return AlgorithmicBreakoutScore(
        total_score=total,
        component_scores=component_scores,
        eligibility_bucket=bucket,
        rejection_reasons=reasons,
        unavailable_components=unavailable,
    )


def score_input_from_feature_row(
    feature_row: dict[str, str],
    *,
    entry_price: float,
    spread: float,
    slippage_per_unit: float,
) -> dict[str, Any]:
    """Build validated algorithmic-score inputs from a CSV feature row."""

    return {
        "entry_price": entry_price,
        "spread": spread,
        "slippage_per_unit": slippage_per_unit,
        "feature_context_H1_trend_alignment": _optional_text(
            feature_row.get("feature_context_H1_trend_alignment")
        ),
        "feature_context_H4_trend_alignment": _optional_text(
            feature_row.get("feature_context_H4_trend_alignment")
        ),
        "feature_context_D1_trend_alignment": _optional_text(
            feature_row.get("feature_context_D1_trend_alignment")
        ),
        "feature_btcusdt_regime_agreement": _optional_float(
            feature_row.get("feature_btcusdt_regime_agreement")
        ),
        "feature_ethusdt_regime_agreement": _optional_float(
            feature_row.get("feature_ethusdt_regime_agreement")
        ),
        "feature_fixed_universe_positive_symbol_ratio": _optional_float(
            feature_row.get("feature_fixed_universe_positive_symbol_ratio")
        ),
        "feature_fixed_universe_breadth_ratio": _optional_float(
            feature_row.get("feature_fixed_universe_breadth_ratio")
        ),
        "feature_relative_strength_vs_btcusdt": _optional_float(
            feature_row.get("feature_relative_strength_vs_btcusdt")
        ),
        "feature_relative_strength_vs_ethusdt": _optional_float(
            feature_row.get("feature_relative_strength_vs_ethusdt")
        ),
        "feature_recent_range_compression": _optional_float(
            feature_row.get("feature_recent_range_compression")
        ),
        "feature_consolidation_range_atr": _optional_float(
            feature_row.get("feature_consolidation_range_atr")
        ),
        "feature_volume_ratio": _optional_float(feature_row.get("feature_volume_ratio")),
        "feature_activity_ratio": _optional_float(feature_row.get("feature_activity_ratio")),
        "feature_breakout_distance_atr": _optional_float(
            feature_row.get("feature_breakout_distance_atr")
        ),
        "feature_ema_slope_atr": _optional_float(feature_row.get("feature_ema_slope_atr")),
    }


def _cost_feasibility(inputs: AlgorithmicBreakoutScoreInput) -> int:
    round_trip_friction = inputs.spread + 2.0 * inputs.slippage_per_unit
    ratio = round_trip_friction / inputs.entry_price
    if ratio <= 0.02:
        return COMPONENT_WEIGHTS["cost_feasibility"]
    if ratio <= 0.04:
        return COMPONENT_WEIGHTS["cost_feasibility"] // 2
    return 0


def _btc_eth_regime(inputs: AlgorithmicBreakoutScoreInput, unavailable: list[str]) -> int:
    numeric = [
        value
        for value in (
            inputs.feature_btcusdt_regime_agreement,
            inputs.feature_ethusdt_regime_agreement,
        )
        if value is not None
    ]
    if numeric:
        return round(COMPONENT_WEIGHTS["btc_eth_regime"] * (sum(numeric) / len(numeric)))
    alignments = [
        inputs.feature_context_H1_trend_alignment,
        inputs.feature_context_H4_trend_alignment,
    ]
    available = [value for value in alignments if value not in {None, "", "unavailable"}]
    if not available:
        unavailable.append("btc_eth_regime")
        return 0
    long_count = sum(1 for value in available if value == "long")
    return round(COMPONENT_WEIGHTS["btc_eth_regime"] * long_count / len(available))


def _market_breadth(inputs: AlgorithmicBreakoutScoreInput, unavailable: list[str]) -> int:
    breadth = inputs.feature_fixed_universe_positive_symbol_ratio
    if breadth is None:
        breadth = inputs.feature_fixed_universe_breadth_ratio
    if breadth is None:
        unavailable.append("market_breadth")
        return 0
    return round(COMPONENT_WEIGHTS["market_breadth"] * min(max(breadth, 0.0), 1.0))


def _relative_strength(inputs: AlgorithmicBreakoutScoreInput, unavailable: list[str]) -> int:
    values = [
        value
        for value in (
            inputs.feature_relative_strength_vs_btcusdt,
            inputs.feature_relative_strength_vs_ethusdt,
        )
        if value is not None
    ]
    if not values:
        unavailable.append("relative_strength")
        return 0
    positive_ratio = sum(1 for value in values if value > 0) / len(values)
    return round(COMPONENT_WEIGHTS["relative_strength"] * positive_ratio)


def _volatility_compression(inputs: AlgorithmicBreakoutScoreInput, unavailable: list[str]) -> int:
    compression = inputs.feature_recent_range_compression
    if compression is None:
        compression = inputs.feature_consolidation_range_atr
    if compression is None:
        unavailable.append("volatility_compression")
        return 0
    if compression <= 1.2:
        return COMPONENT_WEIGHTS["volatility_compression"]
    if compression <= 2.0:
        return round(COMPONENT_WEIGHTS["volatility_compression"] * 0.6)
    if compression <= 3.0:
        return round(COMPONENT_WEIGHTS["volatility_compression"] * 0.3)
    return 0


def _volume_activity(inputs: AlgorithmicBreakoutScoreInput, unavailable: list[str]) -> int:
    volume = inputs.feature_volume_ratio
    if volume is None:
        volume = inputs.feature_activity_ratio
    if volume is None:
        unavailable.append("volume_activity_expansion")
        return 0
    if volume >= 1.5:
        return COMPONENT_WEIGHTS["volume_activity_expansion"]
    if volume >= 1.2:
        return round(COMPONENT_WEIGHTS["volume_activity_expansion"] * 0.7)
    if volume >= 1.0:
        return round(COMPONENT_WEIGHTS["volume_activity_expansion"] * 0.4)
    return 0


def _atr_breakout_distance(inputs: AlgorithmicBreakoutScoreInput, unavailable: list[str]) -> int:
    distance = inputs.feature_breakout_distance_atr
    if distance is None:
        unavailable.append("atr_breakout_distance")
        return 0
    if 0.05 <= distance <= 1.0:
        return COMPONENT_WEIGHTS["atr_breakout_distance"]
    if 0.0 <= distance <= 1.5:
        return round(COMPONENT_WEIGHTS["atr_breakout_distance"] * 0.5)
    return 0


def _multi_timeframe_trend(inputs: AlgorithmicBreakoutScoreInput, unavailable: list[str]) -> int:
    trend_points = 0.0
    trend_count = 0
    if inputs.feature_ema_slope_atr is not None:
        trend_count += 1
        trend_points += 1.0 if inputs.feature_ema_slope_atr > 0 else 0.0
    contexts = [
        inputs.feature_context_H1_trend_alignment,
        inputs.feature_context_H4_trend_alignment,
        inputs.feature_context_D1_trend_alignment,
    ]
    for context in contexts:
        if context in {None, "", "unavailable"}:
            continue
        trend_count += 1
        trend_points += 1.0 if context == "long" else 0.0
    if trend_count == 0:
        unavailable.append("multi_timeframe_trend")
        return 0
    return round(COMPONENT_WEIGHTS["multi_timeframe_trend"] * trend_points / trend_count)


def _optional_float(value: object) -> float | None:
    if value is None or value == "" or value == "unavailable":
        return None
    return float(cast(float | int | str, value))


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
