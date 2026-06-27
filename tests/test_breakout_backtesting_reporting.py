import csv
import json
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from src.app.breakout.backtesting import (
    BacktestEngine,
    daily_trade_summary,
    entry_feature_snapshots,
    evaluate_production_oos_gate,
    feature_bucket_pnl,
    lifecycle_diagnostics,
    path_risk_diagnostic_rows,
    regime_bucket_summary,
    score_bucket_pnl,
    stable_hash,
    weekly_trade_summary,
    worst_day_attribution,
)
from src.core.models import (
    BacktestConfig,
    BacktestConfirmationFilterConfig,
    BacktestCostModel,
    BacktestExitProfileConfig,
    BacktestFeatureFilterConfig,
    BacktestResearchGateConfig,
    BreakoutStrategyConfig,
    ProductionOosThresholds,
    ScoreConfig,
)
from src.core.schemas import Bar


def make_bar(
    index: int, *, high: float, low: float, close: float, open_: float | None = None
) -> Bar:
    return Bar(
        symbol="XAUUSD",
        timeframe="M15",
        ts=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=15 * index),
        open=open_ if open_ is not None else close - 0.2,
        high=high,
        low=low,
        close=close,
        volume=100 + index,
    )


def breakout_dataset() -> list[Bar]:
    return [
        make_bar(0, high=100.0, low=98.0, close=99.0),
        make_bar(1, high=101.0, low=98.5, close=100.0),
        make_bar(2, high=103.0, low=99.0, close=101.0),
        make_bar(3, high=105.0, low=100.0, close=102.0),
        make_bar(4, high=103.0, low=99.5, close=101.0),
        make_bar(5, high=102.0, low=99.0, close=100.5),
        make_bar(6, high=101.5, low=98.5, close=100.0),
        make_bar(7, high=106.0, low=100.0, close=105.5),
        make_bar(8, high=108.0, low=104.0, close=107.0),
        make_bar(9, high=109.0, low=106.0, close=108.0),
        make_bar(10, high=108.5, low=105.0, close=105.5, open_=107.0),
    ]


def config() -> BacktestConfig:
    return BacktestConfig(
        initial_equity=10_000.0,
        base_quantity=10.0,
        stop_distance=2.0,
        min_warmup_bars=7,
        random_seed=42,
        cost_model=BacktestCostModel(
            spread=0.10,
            commission_per_unit=0.01,
            slippage_per_unit=0.02,
            funding_per_bar=0.005,
        ),
        strategy=BreakoutStrategyConfig(
            score=ScoreConfig(threshold_normal=30, threshold_reduced=10)
        ),
        export_parquet=True,
    )


def test_acceptance_quality_backtest_requires_explicit_cost_assumption() -> None:
    with pytest.raises(ValidationError, match="non-zero cost assumptions"):
        BacktestConfig(cost_model=BacktestCostModel())


def test_zero_notional_costs_preserve_existing_per_unit_cost_behavior() -> None:
    report = BacktestEngine(config()).run(breakout_dataset())

    assert report.trades
    for trade in report.trades:
        expected_cost = 0.01 * trade.quantity * 2
        expected_cost += 0.005 * trade.quantity * trade.holding_bars
        expected_cost += 0.10 * trade.quantity
        expected_cost += 0.02 * trade.quantity * 2
        assert trade.total_cost == pytest.approx(expected_cost)


def test_notional_commission_and_funding_are_included_in_trade_costs() -> None:
    base_report = BacktestEngine(config()).run(breakout_dataset())
    notional_config = config().model_copy(
        update={
            "cost_model": BacktestCostModel(
                spread=0.10,
                commission_per_unit=0.01,
                slippage_per_unit=0.02,
                funding_per_bar=0.005,
                commission_rate=0.001,
                funding_rate_per_bar=0.0005,
            )
        }
    )
    notional_report = BacktestEngine(notional_config).run(breakout_dataset())

    base_trade = base_report.trades[0]
    notional_trade = notional_report.trades[0]
    expected_extra_cost = (
        (notional_trade.entry_price + notional_trade.exit_price)
        * notional_trade.quantity
        * 0.001
    ) + (notional_trade.entry_price * notional_trade.quantity * 0.0005 * notional_trade.holding_bars)
    assert notional_trade.total_cost == pytest.approx(base_trade.total_cost + expected_extra_cost)
    assert notional_trade.net_pnl == pytest.approx(base_trade.net_pnl - expected_extra_cost)


def test_backtest_is_deterministic_and_uses_closed_bar_boundary() -> None:
    bars = breakout_dataset()
    engine = BacktestEngine(config())

    early_report = engine.run(bars[:8])
    first_report = engine.run(bars)
    second_report = engine.run(list(reversed(list(reversed(bars)))))

    assert early_report.trades == []
    assert first_report.run_id == second_report.run_id
    assert first_report.dataset_hash == stable_hash(bars)
    assert first_report.config_hash == second_report.config_hash
    assert [trade.model_dump(mode="json") for trade in first_report.trades] == [
        trade.model_dump(mode="json") for trade in second_report.trades
    ]
    assert first_report.trades
    assert all(trade.entry_time < trade.exit_time for trade in first_report.trades)
    assert first_report.monte_carlo is not None
    assert first_report.monte_carlo.seed == 42
    assert "parquet_export" in first_report.unavailable_reasons


def test_report_contains_required_metrics_diagnostics_windows_and_exports(tmp_path) -> None:
    report = BacktestEngine(config()).run(breakout_dataset())
    exported = BacktestEngine(config()).export_report(report, tmp_path)

    assert {
        "cagr",
        "sharpe_ratio",
        "max_drawdown",
        "win_rate",
        "expectancy",
        "average_trade",
        "avg_holding_time",
        "oos_performance",
        "profit_factor",
        "exposure",
    } <= set(report.metrics)
    assert report.equity_curve
    assert report.drawdown_curve
    assert report.return_distribution
    assert report.scenario_breakdown["consolidation_breakout"] >= 1
    assert report.score_distribution["30-39"] >= 1
    assert report.false_breakout_analysis["count"] >= 0
    assert report.slippage_report["configured_per_unit"] == pytest.approx(0.02)
    assert {window.role for window in report.windows} >= {"is", "oos", "train", "forward"}
    expected_names = [
        f"{report.run_id}.json",
        f"{report.run_id}-trades.csv",
        f"{report.run_id}-equity.csv",
        f"{report.run_id}-drawdown.csv",
        f"{report.run_id}-returns.csv",
        f"{report.run_id}-metrics.csv",
        f"{report.run_id}-scenario-breakdown.csv",
        f"{report.run_id}-score-distribution.csv",
        f"{report.run_id}-false-breakout-analysis.csv",
        f"{report.run_id}-slippage-report.csv",
        f"{report.run_id}-daily-summary.csv",
        f"{report.run_id}-weekly-summary.csv",
        f"{report.run_id}-lifecycle-diagnostics.csv",
        f"{report.run_id}-score-bucket-pnl.csv",
        f"{report.run_id}-entry-feature-snapshots.csv",
        f"{report.run_id}-feature-bucket-pnl.csv",
        f"{report.run_id}-regime-bucket-summary.csv",
        f"{report.run_id}-worst-day-attribution.csv",
        f"{report.run_id}-parameters.json",
    ]
    assert [path.split("/")[-1] for path in exported.artifact_paths] == expected_names
    for path in exported.artifact_paths:
        assert (tmp_path / path.split("/")[-1]).exists()

    with (tmp_path / f"{report.run_id}-metrics.csv").open(newline="", encoding="utf-8") as file:
        metrics = {row["metric"]: row["value"] for row in csv.DictReader(file)}
    assert metrics["trade_count"] == str(report.metrics["trade_count"])

    with (tmp_path / f"{report.run_id}-scenario-breakdown.csv").open(
        newline="", encoding="utf-8"
    ) as file:
        scenarios = {row["scenario"]: int(row["count"]) for row in csv.DictReader(file)}
    assert scenarios == report.scenario_breakdown

    with (tmp_path / f"{report.run_id}-parameters.json").open(encoding="utf-8") as file:
        parameters = json.load(file)
    assert parameters == report.parameter_snapshot

    with (tmp_path / f"{report.run_id}-lifecycle-diagnostics.csv").open(
        newline="",
        encoding="utf-8",
    ) as file:
        lifecycle = {row["metric"]: row["value"] for row in csv.DictReader(file)}
    assert lifecycle["total_trades"] == str(len(report.trades))
    assert lifecycle["immediate_reentry_count"] == "2"
    assert lifecycle["holding_bars_distribution"] == "1:3"

    with (tmp_path / f"{report.run_id}-daily-summary.csv").open(
        newline="",
        encoding="utf-8",
    ) as file:
        daily_rows = list(csv.DictReader(file))
    assert daily_rows[0]["trade_count"] == str(len(report.trades))

    with (tmp_path / f"{report.run_id}-weekly-summary.csv").open(
        newline="",
        encoding="utf-8",
    ) as file:
        weekly_rows = list(csv.DictReader(file))
    assert weekly_rows[0]["trade_count"] == str(len(report.trades))

    with (tmp_path / f"{report.run_id}-score-bucket-pnl.csv").open(
        newline="",
        encoding="utf-8",
    ) as file:
        score_rows = list(csv.DictReader(file))
    assert score_rows

    with (tmp_path / f"{report.run_id}-entry-feature-snapshots.csv").open(
        newline="",
        encoding="utf-8",
    ) as file:
        feature_rows = list(csv.DictReader(file))
    assert len(feature_rows) == len(report.trades)
    assert "feature_atr" in feature_rows[0]
    assert "feature_context_H1_available" in feature_rows[0]

    report_json = json.loads((tmp_path / f"{report.run_id}.json").read_text(encoding="utf-8"))
    assert "feature_atr" not in report_json["trades"][0]["metadata"]
    assert "level_price" in report_json["trades"][0]["metadata"]

    with (tmp_path / f"{report.run_id}-feature-bucket-pnl.csv").open(
        newline="",
        encoding="utf-8",
    ) as file:
        feature_bucket_rows = list(csv.DictReader(file))
    assert feature_bucket_rows

    second_export = BacktestEngine(config()).export_report(report, tmp_path)
    assert second_export.artifact_paths == exported.artifact_paths


def test_production_oos_gate_blocks_missing_thresholds() -> None:
    report = BacktestEngine(config()).run(breakout_dataset())

    decision = evaluate_production_oos_gate(report, ProductionOosThresholds())

    assert decision.approved is False
    assert decision.reason == "missing_oos_thresholds"
    assert decision.blockers == ["missing_oos_thresholds"]


def test_production_oos_gate_approves_when_configured_thresholds_pass() -> None:
    report = BacktestEngine(config()).run(breakout_dataset())

    decision = evaluate_production_oos_gate(
        report,
        ProductionOosThresholds(
            min_oos_performance=-10.0,
            min_win_rate=0.0,
            min_trade_count=1,
            max_drawdown_floor=-0.01,
        ),
    )

    assert decision.approved is True
    assert decision.reason == "approved"
    assert {check.metric for check in decision.checked_metrics} == {
        "oos_performance",
        "win_rate",
        "trade_count",
        "max_drawdown",
    }
    assert decision.blockers == []


def test_production_oos_gate_blocks_failed_thresholds() -> None:
    report = BacktestEngine(config()).run(breakout_dataset())

    decision = evaluate_production_oos_gate(
        report,
        ProductionOosThresholds(min_win_rate=1.0, max_drawdown_floor=0.0),
    )

    assert decision.approved is False
    assert decision.reason == "oos_threshold_failed"
    assert "win_rate_below_threshold" in decision.blockers
    assert "max_drawdown_below_threshold" in decision.blockers


def test_production_oos_gate_blocks_missing_or_unavailable_metrics() -> None:
    report = BacktestEngine(config()).run(breakout_dataset())
    missing_metric_report = report.model_copy(update={"metrics": {"win_rate": 0.5}})
    unavailable_metric_report = report.model_copy(
        update={"unavailable_reasons": {"profit_factor": "no losing trades in sample"}}
    )

    missing_decision = evaluate_production_oos_gate(
        missing_metric_report,
        ProductionOosThresholds(min_oos_performance=0.0),
    )
    unavailable_decision = evaluate_production_oos_gate(
        unavailable_metric_report,
        ProductionOosThresholds(min_profit_factor=1.1),
    )

    assert missing_decision.approved is False
    assert missing_decision.reason == "oos_metric_missing"
    assert missing_decision.blockers == ["oos_performance_missing"]
    assert unavailable_decision.approved is False
    assert unavailable_decision.reason == "oos_metric_unavailable"
    assert unavailable_decision.blockers == ["profit_factor_unavailable"]

def test_lifecycle_diagnostic_helpers_group_reentries_and_scores() -> None:
    report = BacktestEngine(config()).run(breakout_dataset())

    diagnostics = lifecycle_diagnostics(report)
    assert diagnostics["total_trades"] == len(report.trades)
    assert diagnostics["immediate_reentry_count"] == max(0, len(report.trades) - 1)
    assert diagnostics["holding_bars_distribution"] == "1:3"
    assert diagnostics["side_distribution"] == "long:3"

    daily_rows = daily_trade_summary(report.trades)
    weekly_rows = weekly_trade_summary(report.trades)
    score_rows = score_bucket_pnl(report.trades)
    assert daily_rows[0]["trade_count"] == len(report.trades)
    assert weekly_rows[0]["trade_count"] == len(report.trades)
    assert sum(int(row["trade_count"]) for row in score_rows) == len(report.trades)


def test_default_research_gates_are_noop() -> None:
    bars = breakout_dataset()
    baseline = BacktestEngine(config()).run(bars)
    gated_config = config().model_copy(update={"research_gates": BacktestResearchGateConfig()})
    gated = BacktestEngine(gated_config).run(bars)

    assert [trade.model_dump(mode="json") for trade in gated.trades] == [
        trade.model_dump(mode="json") for trade in baseline.trades
    ]
    assert gated.parameter_snapshot["research_gate_skip_counts"] == {}


def test_research_gates_reduce_entries_and_record_skip_counts() -> None:
    bars = breakout_dataset()
    gated_config = config().model_copy(
        update={
            "research_gates": BacktestResearchGateConfig(
                min_entry_score=40,
                cooldown_bars_after_trade=1,
                block_immediate_reentry=True,
                max_trades_per_day=1,
            )
        }
    )

    report = BacktestEngine(gated_config).run(bars)

    assert len(report.trades) < len(BacktestEngine(config()).run(bars).trades)
    skip_counts = report.parameter_snapshot["research_gate_skip_counts"]
    assert skip_counts
    assert any(key.startswith("skipped_") for key in skip_counts)


def test_daily_stop_loss_gate_blocks_after_realized_loss() -> None:
    bars = [*breakout_dataset(), make_bar(11, high=110.0, low=104.0, close=109.0)]
    stop_config = config().model_copy(
        update={
            "research_gates": BacktestResearchGateConfig(
                daily_stop_loss=1.0,
            )
        }
    )

    report = BacktestEngine(stop_config).run(bars)

    skip_counts = report.parameter_snapshot["research_gate_skip_counts"]
    assert "skipped_daily_stop_loss" in skip_counts


def test_research_gate_config_rejects_zero_daily_stop_loss() -> None:
    with pytest.raises(ValidationError, match="daily_stop_loss"):
        BacktestResearchGateConfig(daily_stop_loss=0.0)


def test_daily_stop_loss_uses_exit_day_for_midnight_crossing_loss() -> None:
    base = datetime(2026, 1, 1, 21, 30, tzinfo=UTC)
    bars = []
    for index, bar in enumerate([*breakout_dataset(), make_bar(11, high=110.0, low=104.0, close=109.0)]):
        shifted = dict(bar)
        shifted["ts"] = base + timedelta(minutes=15 * index)
        bars.append(Bar(**shifted))
    stop_config = config().model_copy(
        update={
            "research_gates": BacktestResearchGateConfig(
                daily_stop_loss=1.0,
            )
        }
    )

    report = BacktestEngine(stop_config).run(bars)

    assert report.trades[-1].net_pnl < 0
    assert report.trades[-1].entry_time.date() != report.trades[-1].exit_time.date()
    skip_counts = report.parameter_snapshot["research_gate_skip_counts"]
    assert "skipped_daily_stop_loss" in skip_counts


def test_entry_feature_snapshots_include_closed_context_alignment() -> None:
    bars = breakout_dataset()
    entry_time = bars[7]["ts"]
    context = {
        "H1": [
            Bar(**{**bars[0], "timeframe": "H1", "ts": entry_time - timedelta(hours=2), "close": 100.0}),
            Bar(**{**bars[0], "timeframe": "H1", "ts": entry_time - timedelta(minutes=45), "close": 777.0}),
            Bar(**{**bars[0], "timeframe": "H1", "ts": entry_time, "close": 105.0}),
            Bar(**{**bars[0], "timeframe": "H1", "ts": entry_time + timedelta(hours=1), "close": 999.0}),
        ]
    }

    report = BacktestEngine(config(), context_bars=context).run(bars)
    rows = entry_feature_snapshots(report.trades)

    assert rows
    assert rows[0]["feature_context_H1_available"] is True
    assert rows[0]["feature_context_H1_timestamp"] == (entry_time - timedelta(hours=2)).isoformat()
    assert "777" not in str(rows[0])
    assert "105" not in str(rows[0])
    assert "999" not in str(rows[0])


def test_missing_context_feature_markers_do_not_fail_backtest() -> None:
    report = BacktestEngine(config()).run(breakout_dataset())
    row = entry_feature_snapshots(report.trades)[0]

    assert row["feature_context_H1_available"] is False
    assert row["feature_context_H1_reason"] == "not_supplied_or_no_closed_bar"


def test_feature_bucket_regime_and_worst_day_diagnostics_are_deterministic() -> None:
    report = BacktestEngine(config()).run([*breakout_dataset(), make_bar(11, high=110.0, low=80.0, close=100.0)])

    first_buckets = feature_bucket_pnl(report.trades)
    second_buckets = feature_bucket_pnl(report.trades)

    assert first_buckets == second_buckets
    assert regime_bucket_summary(report.trades)
    assert worst_day_attribution(report.trades)


def test_feature_filters_disabled_preserve_trade_selection() -> None:
    base_report = BacktestEngine(config()).run(breakout_dataset())
    filtered_config = config().model_copy(update={"feature_filters": BacktestFeatureFilterConfig()})
    filtered_report = BacktestEngine(filtered_config).run(breakout_dataset())

    assert [trade.trade_id for trade in filtered_report.trades] == [trade.trade_id for trade in base_report.trades]
    assert filtered_report.metrics == base_report.metrics
    assert filtered_report.parameter_snapshot["research_gate_skip_counts"] == {}


def test_m15_ema_slope_filter_skips_non_positive_slope() -> None:
    engine = BacktestEngine(config().model_copy(update={
        "feature_filters": BacktestFeatureFilterConfig(require_m15_ema_slope_positive=True)
    }))

    assert engine._feature_filter_reason({"feature_ema_slope_atr": "unavailable"}) == "skipped_feature_m15_ema_slope_not_positive"
    assert engine._feature_filter_reason({"feature_ema_slope_atr": 0.0}) == "skipped_feature_m15_ema_slope_not_positive"
    assert engine._feature_filter_reason({"feature_ema_slope_atr": -0.1}) == "skipped_feature_m15_ema_slope_not_positive"
    assert engine._feature_filter_reason({"feature_ema_slope_atr": 0.1}) is None


def test_h1_long_filter_skips_missing_or_short_context() -> None:
    engine = BacktestEngine(config().model_copy(update={
        "feature_filters": BacktestFeatureFilterConfig(require_h1_trend_long=True)
    }))

    assert engine._feature_filter_reason({"feature_context_H1_trend_alignment": "unavailable"}) == "skipped_feature_h1_trend_not_long"
    assert engine._feature_filter_reason({"feature_context_H1_trend_alignment": "short_or_flat"}) == "skipped_feature_h1_trend_not_long"
    assert engine._feature_filter_reason({"feature_context_H1_trend_alignment": "long"}) is None


def test_candle_body_cap_filter_skips_unavailable_and_above_cap() -> None:
    engine = BacktestEngine(config().model_copy(update={
        "feature_filters": BacktestFeatureFilterConfig(max_candle_body_ratio=0.75)
    }))

    assert engine._feature_filter_reason({"feature_candle_body_range_ratio": "unavailable"}) == "skipped_feature_candle_body_ratio_unavailable"
    assert engine._feature_filter_reason({"feature_candle_body_range_ratio": 0.8}) == "skipped_feature_candle_body_ratio_above_cap"
    assert engine._feature_filter_reason({"feature_candle_body_range_ratio": 0.75}) is None


def test_atr_percentile_filter_skips_unavailable_and_below_min() -> None:
    engine = BacktestEngine(config().model_copy(update={
        "feature_filters": BacktestFeatureFilterConfig(min_atr_percentile=0.25)
    }))

    assert engine._feature_filter_reason({"feature_atr_percentile": "unavailable"}) == "skipped_feature_atr_percentile_unavailable"
    assert engine._feature_filter_reason({"feature_atr_percentile": 0.25}) == "skipped_feature_atr_percentile_below_min"
    assert engine._feature_filter_reason({"feature_atr_percentile": 0.2501}) is None


def test_breakout_distance_filter_skips_unavailable_and_above_cap() -> None:
    engine = BacktestEngine(config().model_copy(update={
        "feature_filters": BacktestFeatureFilterConfig(max_breakout_distance_atr=1.0)
    }))

    assert engine._feature_filter_reason({"feature_breakout_distance_atr": "unavailable"}) == "skipped_feature_breakout_distance_atr_unavailable"
    assert engine._feature_filter_reason({"feature_breakout_distance_atr": 1.01}) == "skipped_feature_breakout_distance_atr_above_cap"
    assert engine._feature_filter_reason({"feature_breakout_distance_atr": 1.0}) is None


def test_candle_body_min_filter_skips_unavailable_and_below_min() -> None:
    engine = BacktestEngine(config().model_copy(update={
        "feature_filters": BacktestFeatureFilterConfig(min_candle_body_ratio=0.25)
    }))

    assert engine._feature_filter_reason({"feature_candle_body_range_ratio": "unavailable"}) == "skipped_feature_candle_body_ratio_unavailable"
    assert engine._feature_filter_reason({"feature_candle_body_range_ratio": 0.25}) == "skipped_feature_candle_body_ratio_below_min"
    assert engine._feature_filter_reason({"feature_candle_body_range_ratio": 0.2501}) is None


def test_combined_regime_filters_preserve_deterministic_order() -> None:
    engine = BacktestEngine(config().model_copy(update={
        "feature_filters": BacktestFeatureFilterConfig(
            require_m15_ema_slope_positive=True,
            min_atr_percentile=0.25,
            max_breakout_distance_atr=1.0,
            max_candle_body_ratio=0.75,
        )
    }))

    assert engine._feature_filter_reason({"feature_ema_slope_atr": -0.1}) == "skipped_feature_m15_ema_slope_not_positive"
    assert engine._feature_filter_reason({
        "feature_ema_slope_atr": 0.1,
        "feature_atr_percentile": 0.1,
    }) == "skipped_feature_atr_percentile_below_min"
    assert engine._feature_filter_reason({
        "feature_ema_slope_atr": 0.1,
        "feature_atr_percentile": 0.5,
        "feature_breakout_distance_atr": 1.1,
    }) == "skipped_feature_breakout_distance_atr_above_cap"
    assert engine._feature_filter_reason({
        "feature_ema_slope_atr": 0.1,
        "feature_atr_percentile": 0.5,
        "feature_breakout_distance_atr": 0.5,
        "feature_candle_body_range_ratio": 0.8,
    }) == "skipped_feature_candle_body_ratio_above_cap"


def test_confirmation_filters_disabled_preserve_trade_selection() -> None:
    base_report = BacktestEngine(config()).run(breakout_dataset())
    filtered_config = config().model_copy(update={"confirmation_filters": BacktestConfirmationFilterConfig()})
    filtered_report = BacktestEngine(filtered_config).run(breakout_dataset())

    assert [trade.trade_id for trade in filtered_report.trades] == [trade.trade_id for trade in base_report.trades]
    assert filtered_report.metrics == base_report.metrics
    assert filtered_report.parameter_snapshot["research_gate_skip_counts"] == {}


def test_one_close_confirmation_delays_entry_without_lookahead() -> None:
    base_report = BacktestEngine(config()).run(breakout_dataset())
    confirmed_config = config().model_copy(update={
        "confirmation_filters": BacktestConfirmationFilterConfig(required_closes_above_breakout=1)
    })
    confirmed_report = BacktestEngine(confirmed_config).run(breakout_dataset())

    assert base_report.trades
    assert len(confirmed_report.trades) == 1
    trade = confirmed_report.trades[0]
    assert trade.entry_time > base_report.trades[0].entry_time
    assert trade.metadata["feature_confirmation_candidate_index"] == 7
    assert trade.metadata["feature_confirmation_entry_delay_bars"] == 1
    assert trade.metadata["feature_confirmation_closes"] == 1


def test_two_close_confirmation_requires_consecutive_closes() -> None:
    confirmed_config = config().model_copy(update={
        "confirmation_filters": BacktestConfirmationFilterConfig(required_closes_above_breakout=2)
    })
    confirmed_report = BacktestEngine(confirmed_config).run(breakout_dataset())

    assert len(confirmed_report.trades) == 1
    trade = confirmed_report.trades[0]
    assert trade.metadata["feature_confirmation_entry_delay_bars"] == 2
    assert trade.metadata["feature_confirmation_closes"] == 2


def test_confirmation_close_position_filter_and_zero_range_failure() -> None:
    confirmed_config = config().model_copy(update={
        "confirmation_filters": BacktestConfirmationFilterConfig(
            required_closes_above_breakout=1,
            min_close_position=0.70,
        )
    })
    confirmed_report = BacktestEngine(confirmed_config).run(breakout_dataset())
    assert len(confirmed_report.trades) == 1

    zero_range_bars = breakout_dataset()
    zero_range_bars[8] = make_bar(8, high=107.0, low=107.0, close=107.0, open_=107.0)
    zero_range_report = BacktestEngine(confirmed_config).run(zero_range_bars)
    assert zero_range_report.trades == []
    assert zero_range_report.parameter_snapshot["research_gate_skip_counts"] == {
        "skipped_confirmation_close_position_unavailable": 1
    }


def test_confirmation_return_inside_range_cancels_candidate() -> None:
    confirmed_config = config().model_copy(update={
        "confirmation_filters": BacktestConfirmationFilterConfig(
            required_closes_above_breakout=1,
            cancel_on_return_inside_range=True,
        )
    })
    confirmed_report = BacktestEngine(confirmed_config).run(breakout_dataset())

    assert confirmed_report.trades == []
    assert confirmed_report.parameter_snapshot["research_gate_skip_counts"] == {
        "skipped_confirmation_returned_inside_range": 1
    }


def test_exit_profile_fixed_holding_and_atr_thresholds_are_research_only() -> None:
    bars = [*breakout_dataset(), make_bar(11, high=112.0, low=104.0, close=111.0)]
    base_report = BacktestEngine(config()).run(bars)
    hold_config = config().model_copy(
        update={"exit_profile": BacktestExitProfileConfig(fixed_holding_bars=2)}
    )
    hold_report = BacktestEngine(hold_config).run(bars)

    assert [trade.entry_time for trade in hold_report.trades] == [
        trade.entry_time for trade in base_report.trades
    ]
    assert hold_report.trades[0].holding_bars == 2
    assert hold_report.trades[0].exit_time == bars[9]["ts"]
    assert hold_report.trades[0].metadata["exit_reason"] == "fixed_holding_close"
    assert "fixed_holding_close" in str(hold_report.parameter_snapshot["exit_profile_counts"])

    target_config = config().model_copy(
        update={
            "exit_profile": BacktestExitProfileConfig(
                fixed_holding_bars=4,
                stop_atr=1.0,
                target_atr=1.5,
            )
        }
    )
    target_report = BacktestEngine(target_config).run(bars)
    assert target_report.trades[0].metadata["exit_reason"] in {"atr_stop", "atr_target"}

def test_exit_profile_uses_conservative_same_bar_stop_first() -> None:
    bars = [
        *breakout_dataset(),
        make_bar(11, high=120.0, low=90.0, close=110.0),
        make_bar(12, high=111.0, low=109.0, close=110.0),
    ]
    exit_config = config().model_copy(
        update={
            "exit_profile": BacktestExitProfileConfig(
                fixed_holding_bars=4,
                stop_atr=0.1,
                target_atr=0.1,
            )
        }
    )

    report = BacktestEngine(exit_config).run(bars)

    assert report.trades[0].metadata["exit_reason"] == "atr_stop"
    assert report.trades[0].net_pnl < 0


def test_exit_profile_missing_atr_and_no_threshold_hit_fall_back_to_max_hold() -> None:
    future_bars = [
        make_bar(8, high=107.2, low=106.8, close=107.0),
        make_bar(9, high=107.3, low=106.9, close=107.1),
        make_bar(10, high=107.4, low=107.0, close=107.2),
        make_bar(11, high=107.5, low=107.1, close=107.3),
    ]
    engine = BacktestEngine(
        config().model_copy(
            update={
                "exit_profile": BacktestExitProfileConfig(
                    fixed_holding_bars=4,
                    stop_atr=1.0,
                    target_atr=1.5,
                )
            }
        )
    )

    exit_bar, raw_exit_price, holding_bars, exit_reason = engine._resolve_exit(
        entry_price=107.0,
        next_bar=future_bars[0],
        future_bars=future_bars,
        feature_snapshot={"feature_atr": "unavailable"},
    )
    assert exit_bar == future_bars[3]
    assert raw_exit_price == pytest.approx(107.3)
    assert holding_bars == 4
    assert exit_reason == "missing_entry_atr_fixed_holding_close"

    exit_bar, raw_exit_price, holding_bars, exit_reason = engine._resolve_exit(
        entry_price=107.0,
        next_bar=future_bars[0],
        future_bars=future_bars,
        feature_snapshot={"feature_atr": 10.0},
    )
    assert exit_bar == future_bars[3]
    assert raw_exit_price == pytest.approx(107.3)
    assert holding_bars == 4
    assert exit_reason == "fixed_holding_close"


def test_forward_path_diagnostics_are_opt_in_and_do_not_change_trades(tmp_path) -> None:
    bars = breakout_dataset()
    base_report = BacktestEngine(config()).run(bars)
    diagnostic_config = config().model_copy(update={"forward_path_diagnostics": True})
    diagnostic_engine = BacktestEngine(diagnostic_config)
    diagnostic_report = diagnostic_engine.run(bars)

    assert [(trade.entry_time, trade.exit_time, trade.entry_price, trade.exit_price) for trade in diagnostic_report.trades] == [
        (trade.entry_time, trade.exit_time, trade.entry_price, trade.exit_price) for trade in base_report.trades
    ]
    assert diagnostic_report.metrics == base_report.metrics
    assert len(diagnostic_report.forward_path_diagnostics) == len(base_report.trades) * 5
    first_horizon = diagnostic_report.forward_path_diagnostics[0]
    assert first_horizon["trade_id"] == diagnostic_report.trades[0].trade_id
    assert first_horizon["horizon_bars"] == 1
    assert first_horizon["available"] is True
    trade = diagnostic_report.trades[0]
    assert first_horizon["forward_return"] == pytest.approx((107.0 - trade.entry_price) / trade.entry_price)
    assert first_horizon["mfe"] == pytest.approx(108.0 - trade.entry_price)
    assert first_horizon["mae"] == pytest.approx(104.0 - trade.entry_price)
    assert first_horizon["time_to_mfe_bars"] == 1
    assert first_horizon["time_to_mae_bars"] == 1
    assert first_horizon["returned_to_breakout_level"] is True
    assert first_horizon["crossed_below_entry"] is True

    exported = diagnostic_engine.export_report(diagnostic_report, tmp_path)
    forward_paths = [path for path in exported.artifact_paths if path.endswith("-forward-path-diagnostics.csv")]
    holding_paths = [path for path in exported.artifact_paths if path.endswith("-holding-horizon-pnl.csv")]
    assert len(forward_paths) == 1
    assert len(holding_paths) == 1

    with open(forward_paths[0], newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["trade_id"] == diagnostic_report.trades[0].trade_id
    assert rows[0]["horizon_bars"] == "1"


def test_forward_path_records_unavailable_horizons() -> None:
    report = BacktestEngine(
        config().model_copy(update={"forward_path_diagnostics": True, "forward_path_horizons": (1, 16)})
    ).run(breakout_dataset())

    unavailable = [
        row
        for row in report.forward_path_diagnostics
        if row["available"] is False and row["horizon_bars"] == 16
    ]
    assert unavailable
    assert {row["unavailable_reason"] for row in unavailable} == {"insufficient_future_bars"}
    horizon_summary = {row["horizon_bars"]: row for row in report.holding_horizon_diagnostics}
    assert horizon_summary[16]["unavailable_count"] == len(report.trades)
    assert horizon_summary[16]["available_count"] == 0
    assert horizon_summary[16]["average_forward_return"] == "unavailable"


def test_path_risk_diagnostics_are_opt_in_and_do_not_change_trades(tmp_path) -> None:
    bars = breakout_dataset()
    base_report = BacktestEngine(config()).run(bars)
    diagnostic_config = config().model_copy(update={"path_risk_diagnostics": True})
    diagnostic_engine = BacktestEngine(diagnostic_config)
    diagnostic_report = diagnostic_engine.run(bars)

    assert [(trade.entry_time, trade.exit_time, trade.entry_price, trade.exit_price) for trade in diagnostic_report.trades] == [
        (trade.entry_time, trade.exit_time, trade.entry_price, trade.exit_price) for trade in base_report.trades
    ]
    assert diagnostic_report.metrics == base_report.metrics
    assert diagnostic_report.path_risk_diagnostics
    first = diagnostic_report.path_risk_diagnostics[0]
    assert first["available"] is True
    assert first["horizon_bars"] == 1
    assert first["entry_atr"] != "unavailable"
    assert first["favorable_0p5_hit"] is True
    assert first["adverse_0p5_hit"] in {True, False}
    assert first["fav_1p0_before_adv_1p0"] in {True, False, "same_bar"}
    assert first["breakeven_reachable"] in {True, False}
    assert "trail_after_fav_1p0_giveback_0p5_touched" in first

    exported = diagnostic_engine.export_report(diagnostic_report, tmp_path)
    assert any(path.endswith("-path-risk-diagnostics.csv") for path in exported.artifact_paths)
    assert any(path.endswith("-path-risk-threshold-summary.csv") for path in exported.artifact_paths)


def test_path_risk_records_missing_atr_and_insufficient_future_bars() -> None:
    bars = breakout_dataset()
    report = BacktestEngine(
        config().model_copy(update={"path_risk_diagnostics": True, "forward_path_horizons": (1, 16)})
    ).run(bars)
    missing_atr_trade = report.trades[0].model_copy(
        update={"metadata": {**report.trades[0].metadata, "feature_atr": "unavailable"}}
    )
    custom_report = BacktestEngine(
        config().model_copy(update={"path_risk_diagnostics": True, "forward_path_horizons": (1,)})
    ).run(bars)
    # Directly verify generated labels by rebuilding through a tiny exported report copy.
    assert any(row["unavailable_reason"] == "insufficient_future_bars" for row in report.path_risk_diagnostics)
    rows = path_risk_diagnostic_rows(bars, [missing_atr_trade], horizons=(1,))
    assert rows[0]["available"] is False
    assert rows[0]["unavailable_reason"] == "missing_entry_atr"
    assert custom_report.path_risk_threshold_summary
