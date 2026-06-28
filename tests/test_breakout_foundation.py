from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from src.app.breakout.level_engine import LevelEngine
from src.app.breakout.normalizer import Normalizer
from src.app.breakout.setup_scoring import SetupEvaluator
from src.core.enums import LevelType, OperationMode, ScenarioType, Side, TimeFrame
from src.core.models import (
    BreakoutStrategyConfig,
    ContextDriverSignal,
    ContextFilterConfig,
    FeatureVector,
    LevelDetectionConfig,
    SetupConfig,
)
from src.core.schemas import Bar, OrderBookLevel


def make_bar(index: int, *, high: float, low: float, close: float | None = None) -> Bar:
    return Bar(
        symbol="XAUUSD",
        timeframe="M15",
        ts=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=15 * index),
        open=(high + low) / 2,
        high=high,
        low=low,
        close=close if close is not None else (high + low) / 2,
        volume=100.0,
    )


def test_default_breakout_config_matches_foundation_contract() -> None:
    config = BreakoutStrategyConfig()

    assert config.mode is OperationMode.SEMI_AUTO
    assert config.full_auto_contract_validation_only is False
    assert config.execution_timeframe is TimeFrame.M15
    assert config.context_timeframes == [TimeFrame.H1, TimeFrame.H4, TimeFrame.D1]
    assert config.model_dump(mode="json")["mode"] == "semi_auto"
    assert config.setup.protorgovka_range_percent == (0.3, 2.0)
    assert config.entries.pre_entry_share == pytest.approx(0.30)
    assert config.entries.at_level_share == pytest.approx(0.30)
    assert config.entries.post_breakout_share == pytest.approx(0.40)
    assert config.score.threshold_normal == 70
    assert config.score.threshold_reduced == 50


def test_unapproved_full_auto_config_is_blocked_with_explicit_reason() -> None:
    with pytest.raises(ValidationError, match="dedicated full-auto OpenSpec change"):
        BreakoutStrategyConfig(mode=OperationMode.FULL_AUTO)


def test_full_auto_contract_can_be_instantiated_only_for_contract_validation() -> None:
    config = BreakoutStrategyConfig(
        mode=OperationMode.FULL_AUTO,
        full_auto_contract_validation_only=True,
    )

    assert config.mode is OperationMode.FULL_AUTO
    assert config.full_auto_contract_validation_only is True


def test_entry_shares_must_sum_to_one() -> None:
    with pytest.raises(ValidationError):
        BreakoutStrategyConfig.model_validate(
            {
                "entries": {
                    "pre_entry_share": 0.3,
                    "at_level_share": 0.3,
                    "post_breakout_share": 0.3,
                }
            }
        )


def test_normalizer_converts_timestamps_deduplicates_and_detects_gaps() -> None:
    normalizer = Normalizer()
    raw = [
        {"time": 1_767_225_600, "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 10},
        {"time": 1_767_225_600, "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 10},
        {"time": 1_767_227_400, "open": 2, "high": 3, "low": 1.5, "close": 2.5, "volume": 11},
    ]
    bars = [normalizer.normalize_bar(item, symbol="BTCUSDT", timeframe="M15") for item in raw]

    deduped = normalizer.deduplicate_bars(bars)
    gaps = normalizer.detect_bar_gaps(deduped)

    assert len(deduped) == 2
    assert deduped[0]["ts"].tzinfo == UTC
    assert len(gaps) == 1
    assert gaps[0]["expected_seconds"] == 900
    assert gaps[0]["actual_seconds"] == 1800


def test_normalizer_validates_order_and_deduplicates_ticks() -> None:
    normalizer = Normalizer()
    first = normalizer.normalize_tick({"time": 10, "bid": 1.0, "ask": 1.1}, symbol="EURUSD")
    duplicate = normalizer.normalize_tick({"time": 10, "last": 1.05}, symbol="EURUSD")
    later = normalizer.normalize_tick({"time": 11, "last": 1.06}, symbol="EURUSD")

    assert normalizer.deduplicate_ticks([later, first, duplicate]) == [duplicate, later]
    with pytest.raises(ValueError, match="out of order"):
        normalizer.validate_bar_order([make_bar(1, high=11, low=10), make_bar(0, high=11, low=10)])


def test_pivot_detection_waits_for_right_window_no_lookahead() -> None:
    bars = [
        make_bar(0, high=10, low=5),
        make_bar(1, high=11, low=6),
        make_bar(2, high=15, low=7),
        make_bar(3, high=12, low=6),
        make_bar(4, high=11, low=5),
    ]
    engine = LevelEngine(LevelDetectionConfig(pivot_left_bars=2, pivot_right_bars=2))

    early_levels = engine.detect_pivots(bars, as_of_index=3)
    confirmed_levels = engine.detect_pivots(bars, as_of_index=4)

    assert not any(level.type == LevelType.PIVOT_HIGH for level in early_levels)
    pivot_highs = [level for level in confirmed_levels if level.type == LevelType.PIVOT_HIGH]
    assert len(pivot_highs) == 1
    assert pivot_highs[0].price == 15
    assert pivot_highs[0].source_indexes == [2]


def test_round_and_daily_levels_are_detected() -> None:
    bars = [
        make_bar(0, high=101.2, low=99.8),
        Bar(
            symbol="XAUUSD",
            timeframe="D1",
            ts=datetime(2026, 1, 2, tzinfo=UTC),
            open=100,
            high=105,
            low=95,
            close=101,
            volume=1000,
        ),
    ]
    engine = LevelEngine()

    round_levels = engine.detect_round_levels(bars[:1], round_step=1.0)
    daily_levels = engine.detect_daily_levels(bars)

    assert {level.price for level in round_levels} >= {100.0, 101.0}
    assert {level.type for level in daily_levels} == {LevelType.DAILY_HIGH, LevelType.DAILY_LOW}


def test_cascade_trendline_and_recent_break_validation_are_auditable() -> None:
    engine = LevelEngine(LevelDetectionConfig(cascade_min_count=2, cascade_gap_atr=1.0))
    levels = [
        engine._make_level(make_bar(0, high=101, low=99, close=100), LevelType.PIVOT_HIGH, 100.0, 0),
        engine._make_level(make_bar(1, high=102, low=100, close=101), LevelType.PIVOT_HIGH, 100.8, 1),
        engine._make_level(make_bar(2, high=103, low=101, close=102), LevelType.PIVOT_HIGH, 101.6, 2),
    ]

    cascades = engine.detect_cascade_levels(levels, atr=1.0)
    trendlines = engine.detect_trendline_levels(levels, tolerance_atr=0.1, atr=1.0)
    invalid = engine.validate_level(levels[0], [make_bar(3, high=103, low=101, close=102)], atr=1.0)

    assert cascades[0].type is LevelType.CASCADE
    assert cascades[0].metadata["component_count"] == 3
    assert trendlines[0].type is LevelType.TRENDLINE
    assert trendlines[0].touches == 3
    assert invalid.invalidated_at is not None
    assert invalid.invalidation_reason == "recent_break"


def test_setup_score_buckets_normal_reduced_and_blocked() -> None:
    evaluator = SetupEvaluator()
    strong = FeatureVector(
        symbol="XAUUSD",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        atr=1.0,
        ema_fast=105,
        ema_slow=100,
        adx=30,
        consolidation_range_atr=1.0,
        approach_velocity=0.2,
        activity_ratio=1.3,
        density_available=True,
        density_supports_breakout=True,
    )
    medium = strong.model_copy(update={"activity_ratio": 0.5, "density_supports_breakout": False})
    weak = strong.model_copy(
        update={
            "ema_fast": 95,
            "ema_slow": 100,
            "consolidation_range_atr": 3.0,
            "approach_velocity": 1.0,
            "activity_ratio": 0.5,
            "density_supports_breakout": False,
        }
    )

    assert evaluator.score(strong, side=Side.LONG).eligibility == "normal"
    assert evaluator.score(medium, side=Side.LONG).eligibility == "reduced"
    blocked = evaluator.score(weak, side=Side.LONG)
    assert blocked.eligibility == "blocked"
    assert blocked.rejection_reasons == ["score_too_low"]


def test_setup_feature_calculation_and_scenario_priority() -> None:
    evaluator = SetupEvaluator()
    bars = [make_bar(index, high=100 + index * 0.2, low=99 + index * 0.2, close=99.5 + index * 0.2) for index in range(15)]
    order_book: list[OrderBookLevel] = [
        {"symbol": "XAUUSD", "ts": bars[-1]["ts"], "side": "bid", "price": 102, "volume": 20},
        {"symbol": "XAUUSD", "ts": bars[-1]["ts"], "side": "ask", "price": 103, "volume": 10},
    ]

    features = evaluator.calculate_features(bars, order_book=order_book, side=Side.LONG)
    scenario = evaluator.select_scenario(
        {ScenarioType.DENSITY_SUPPORTED_BREAKOUT, ScenarioType.CONSOLIDATION_BREAKOUT}
    )

    assert features.atr > 0
    assert features.ema_fast is not None
    assert features.ema_slow is not None
    assert features.adx is not None
    assert features.density_supports_breakout is True
    assert scenario is ScenarioType.CONSOLIDATION_BREAKOUT


def test_ohlcv_density_proxy_is_scale_invariant_and_reports_source() -> None:
    evaluator = SetupEvaluator()

    def scaled_bars(symbol: str, scale: float) -> list[Bar]:
        bars: list[Bar] = []
        for index in range(20):
            base = (100.0 + index * 0.02) * scale
            bar = make_bar(
                index,
                high=base + 0.5 * scale,
                low=base - 0.5 * scale,
                close=base + 0.35 * scale,
            )
            bars.append(
                Bar(
                    **{
                        **bar,
                        "symbol": symbol,
                        "open": base - 0.25 * scale,
                        "volume": 100.0 + index,
                    }
                )
            )
        return bars

    low_price = evaluator.calculate_features(scaled_bars("LOWUSDT", 1.0), level_price=100.0)
    high_price = evaluator.calculate_features(scaled_bars("HIGHUSDT", 100.0), level_price=10_000.0)

    assert low_price.density_source == "ohlcv_proxy"
    assert high_price.density_source == "ohlcv_proxy"
    assert low_price.normalized_threshold_mode == "rolling_percentiles"
    assert low_price.missing_feature_blockers == []
    assert high_price.missing_feature_blockers == []
    assert low_price.body_dominance == pytest.approx(high_price.body_dominance)
    assert low_price.wick_rejection == pytest.approx(high_price.wick_rejection)
    assert low_price.close_location_quality == pytest.approx(high_price.close_location_quality)
    assert low_price.relative_volume_expansion == pytest.approx(high_price.relative_volume_expansion)
    score = evaluator.score(low_price)
    assert score.density_source == "ohlcv_proxy"
    assert score.density_proxy_components["body_dominance"] == pytest.approx(
        low_price.body_dominance
    )
    assert score.normalized_threshold_mode == "rolling_percentiles"


def test_ohlcv_density_proxy_is_side_aware_for_body_wick_and_close_quality() -> None:
    evaluator = SetupEvaluator()
    bars = [make_bar(index, high=100.4, low=99.6, close=100.0) for index in range(19)]
    breakout = Bar(
        **{
            **make_bar(19, high=101.0, low=99.0, close=100.8),
            "open": 99.1,
            "volume": 180.0,
        }
    )
    long_features = evaluator.calculate_features([*bars, breakout], level_price=100.0, side=Side.LONG)
    short_features = evaluator.calculate_features([*bars, breakout], level_price=100.0, side=Side.SHORT)

    assert long_features.body_dominance == pytest.approx(0.85)
    assert long_features.close_location_quality is not None
    assert short_features.close_location_quality is not None
    assert long_features.wick_rejection is not None
    assert short_features.wick_rejection is not None
    assert long_features.close_location_quality > short_features.close_location_quality
    assert long_features.wick_rejection > short_features.wick_rejection


def test_calibration_artifact_blocks_when_window_reaches_candidate_time() -> None:
    bars = [make_bar(index, high=101.0, low=99.0, close=100.0) for index in range(20)]
    config = SetupConfig(
        normalization_mode="calibration_artifact",
        calibration_artifact_path="artifacts/calibration/BTCUSDT.json",
        calibration_window_start=bars[0]["ts"],
        calibration_window_end=bars[-1]["ts"],
    )
    evaluator = SetupEvaluator(setup_config=config)

    features = evaluator.calculate_features(bars, level_price=100.0)
    score = evaluator.score(features)

    assert features.calibration_artifact_path == "artifacts/calibration/BTCUSDT.json"
    assert features.missing_feature_blockers == ["calibration_window_not_closed_before_candidate"]
    assert score.eligibility == "blocked"
    assert "calibration_window_not_closed_before_candidate" in score.rejection_reasons


def test_setup_score_is_side_symmetric_for_trend() -> None:
    evaluator = SetupEvaluator()
    features = FeatureVector(
        symbol="XAUUSD",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        atr=1.0,
        ema_fast=95,
        ema_slow=100,
        adx=30,
        consolidation_range_atr=1.0,
        approach_velocity=0.2,
        activity_ratio=1.3,
        density_available=True,
        density_supports_breakout=True,
    )

    long_score = evaluator.score(features, side=Side.LONG)
    short_score = evaluator.score(features, side=Side.SHORT)

    assert long_score.trend == 0
    assert short_score.trend == 20


def test_context_filter_penalizes_or_blocks_only_opposed_side() -> None:
    evaluator = SetupEvaluator(
        context_config=ContextFilterConfig(hard_block_threshold=0.80, full_strength_penalty=20)
    )
    features = FeatureVector(
        symbol="XAUUSD",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        atr=1.0,
        ema_fast=105,
        ema_slow=100,
        adx=30,
        consolidation_range_atr=1.0,
        approach_velocity=0.2,
        activity_ratio=1.3,
        density_available=True,
        density_supports_breakout=True,
    )
    moderate_opposition = ContextDriverSignal(
        name="DXY",
        opposes_side=Side.LONG,
        strength=0.50,
        reason="dollar_bid_against_long_gold",
    )
    strong_opposition = moderate_opposition.model_copy(update={"strength": 0.90})

    penalized = evaluator.score(features, side=Side.LONG, context_drivers=[moderate_opposition])
    blocked = evaluator.score(features, side=Side.LONG, context_drivers=[strong_opposition])
    unaffected_short = evaluator.score(features, side=Side.SHORT, context_drivers=[strong_opposition])

    assert penalized.total == 90
    assert penalized.eligibility == "normal"
    assert penalized.rejection_reasons == [
        "context_filter_penalty",
        "context_driver:DXY:dollar_bid_against_long_gold",
    ]
    assert blocked.total == 100
    assert blocked.eligibility == "blocked"
    assert blocked.rejection_reasons == [
        "context_filter_blocked",
        "context_driver:DXY:dollar_bid_against_long_gold",
    ]
    assert unaffected_short.rejection_reasons == []
