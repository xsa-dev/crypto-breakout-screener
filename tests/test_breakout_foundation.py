from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from src.app.breakout.level_engine import LevelEngine
from src.app.breakout.normalizer import Normalizer
from src.app.breakout.setup_scoring import SetupEvaluator
from src.core.enums import LevelType, OperationMode, Side, TimeFrame
from src.core.models import BreakoutStrategyConfig, FeatureVector, LevelDetectionConfig
from src.core.schemas import Bar


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
    assert config.execution_timeframe is TimeFrame.M15
    assert config.context_timeframes == [TimeFrame.H1, TimeFrame.H4, TimeFrame.D1]
    assert config.model_dump(mode="json")["mode"] == "semi_auto"
    assert config.setup.protorgovka_range_percent == (0.3, 2.0)
    assert config.entries.pre_entry_share == pytest.approx(0.30)
    assert config.entries.at_level_share == pytest.approx(0.30)
    assert config.entries.post_breakout_share == pytest.approx(0.40)
    assert config.score.threshold_normal == 70
    assert config.score.threshold_reduced == 50


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
    assert evaluator.score(weak, side=Side.LONG).eligibility == "blocked"


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
