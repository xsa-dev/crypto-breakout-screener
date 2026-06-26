import csv
import json
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from src.app.breakout.backtesting import (
    BacktestEngine,
    daily_trade_summary,
    evaluate_production_oos_gate,
    lifecycle_diagnostics,
    score_bucket_pnl,
    stable_hash,
    weekly_trade_summary,
)
from src.core.models import (
    BacktestConfig,
    BacktestCostModel,
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
