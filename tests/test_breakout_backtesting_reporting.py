import csv
import json
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from src.app.breakout.backtesting import BacktestEngine, stable_hash
from src.core.models import BacktestConfig, BacktestCostModel, BreakoutStrategyConfig, ScoreConfig
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

    second_export = BacktestEngine(config()).export_report(report, tmp_path)
    assert second_export.artifact_paths == exported.artifact_paths
