"""Deterministic local backtesting and report exports for breakout research."""

import csv
import hashlib
import json
import random
from collections.abc import Mapping, Sequence
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel

from src.app.breakout.entry_engine import EntryEngine
from src.app.breakout.level_engine import LevelEngine
from src.app.breakout.risk_manager import RiskManager
from src.app.breakout.setup_scoring import SetupEvaluator
from src.core.enums import ScenarioType, Side
from src.core.models import (
    BacktestConfig,
    BacktestCostModel,
    BacktestReport,
    BacktestTrade,
    BacktestWindow,
    BreakoutScore,
    MarketSnapshot,
    MonteCarloResult,
    ProductionOosGateDecision,
    ProductionOosMetricCheck,
    ProductionOosThresholds,
    RiskLimits,
    RiskState,
)
from src.core.schemas import Bar


class BacktestEngine:
    """Closed-bar deterministic replay engine with no live broker side effects."""

    def __init__(self, config: BacktestConfig | None = None) -> None:
        self.config = config or BacktestConfig(
            cost_model=BacktestCostModel(spread=0.01, slippage_per_unit=0.01)
        )
        self.level_engine = LevelEngine(self.config.strategy.level_detection)
        self.setup_evaluator = SetupEvaluator(
            self.config.strategy.score,
            setup_config=self.config.strategy.setup,
            trend_config=self.config.strategy.trend_filter,
        )
        self.entry_engine = EntryEngine(self.config.strategy)
        self.risk_manager = RiskManager(RiskLimits(equity=self.config.initial_equity))

    def run(self, bars: Sequence[Bar]) -> BacktestReport:
        """Replay bars using only data available at each simulated timestamp."""

        ordered = sorted(bars, key=lambda bar: bar["ts"])
        if len(ordered) <= self.config.min_warmup_bars:
            msg = "not enough closed bars for configured warmup"
            raise ValueError(msg)

        dataset_hash = stable_hash(ordered)
        config_hash = stable_hash(self.config)
        trades: list[BacktestTrade] = []
        equity = self.config.initial_equity
        equity_curve: list[dict[str, float | str]] = [
            {"timestamp": ordered[0]["ts"].isoformat(), "equity": equity}
        ]
        unavailable: dict[str, str] = {}

        for index in range(self.config.min_warmup_bars, len(ordered) - 1):
            history = ordered[: index + 1]
            current = ordered[index]
            next_bar = ordered[index + 1]
            trade = self._evaluate_closed_bar(history, current, next_bar, index, config_hash)
            if trade is None:
                equity_curve.append({"timestamp": current["ts"].isoformat(), "equity": equity})
                continue
            trades.append(trade)
            equity += trade.net_pnl
            equity_curve.append({"timestamp": trade.exit_time.isoformat(), "equity": equity})

        windows = self._validation_windows(len(ordered))
        monte_carlo = self.monte_carlo(trades, seed=self.config.random_seed, iterations=100)
        if self.config.export_parquet:
            unavailable["parquet_export"] = "parquet dependency is not present in this project"

        return build_report(
            run_id=self._run_id(config_hash, dataset_hash),
            config_hash=config_hash,
            dataset_hash=dataset_hash,
            config=self.config,
            bars=ordered,
            trades=trades,
            equity_curve=equity_curve,
            windows=windows,
            monte_carlo=monte_carlo,
            unavailable_reasons=unavailable,
        )

    def monte_carlo(
        self,
        trades: Sequence[BacktestTrade],
        *,
        seed: int,
        iterations: int,
    ) -> MonteCarloResult:
        """Perturb trade order with seeded randomness for reproducible robustness output."""

        rng = random.Random(seed)
        totals: list[float] = []
        pnl_values = [trade.net_pnl for trade in trades]
        for _ in range(iterations):
            sample = list(pnl_values)
            rng.shuffle(sample)
            totals.append(sum(sample))
        if not totals:
            totals = [0.0]
        ordered = sorted(totals)
        median = ordered[len(ordered) // 2]
        return MonteCarloResult(
            seed=seed,
            iterations=iterations,
            method="seeded_trade_order_permutation",
            median_net_pnl=median,
            worst_net_pnl=ordered[0],
            best_net_pnl=ordered[-1],
        )

    def export_report(self, report: BacktestReport, output_dir: str | Path) -> BacktestReport:
        """Write deterministic JSON and CSV artifacts and return report with paths."""

        directory = Path(output_dir)
        directory.mkdir(parents=True, exist_ok=True)
        report_path = directory / f"{report.run_id}.json"
        trades_path = directory / f"{report.run_id}-trades.csv"
        equity_path = directory / f"{report.run_id}-equity.csv"
        drawdown_path = directory / f"{report.run_id}-drawdown.csv"
        returns_path = directory / f"{report.run_id}-returns.csv"
        metrics_path = directory / f"{report.run_id}-metrics.csv"
        scenario_path = directory / f"{report.run_id}-scenario-breakdown.csv"
        score_path = directory / f"{report.run_id}-score-distribution.csv"
        false_breakout_path = directory / f"{report.run_id}-false-breakout-analysis.csv"
        slippage_path = directory / f"{report.run_id}-slippage-report.csv"
        parameters_path = directory / f"{report.run_id}-parameters.json"

        report_path.write_text(
            json.dumps(_normalize(report), sort_keys=True, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        with trades_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "trade_id",
                    "symbol",
                    "side",
                    "entry_time",
                    "exit_time",
                    "entry_price",
                    "exit_price",
                    "quantity",
                    "gross_pnl",
                    "total_cost",
                    "net_pnl",
                    "holding_bars",
                    "scenario",
                    "score",
                    "slippage",
                ],
            )
            writer.writeheader()
            for trade in report.trades:
                payload = trade.model_dump(mode="json")
                payload.pop("metadata", None)
                writer.writerow(payload)
        with equity_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["timestamp", "equity"])
            writer.writeheader()
            writer.writerows(report.equity_curve)

        _write_csv_rows(drawdown_path, ["timestamp", "drawdown"], report.drawdown_curve)
        _write_csv_rows(
            returns_path,
            ["index", "return"],
            [
                {"index": index, "return": value}
                for index, value in enumerate(report.return_distribution)
            ],
        )
        _write_metric_csv(metrics_path, "metric", report.metrics)
        _write_metric_csv(scenario_path, "scenario", report.scenario_breakdown, value_name="count")
        _write_metric_csv(score_path, "bucket", report.score_distribution, value_name="count")
        _write_metric_csv(false_breakout_path, "metric", report.false_breakout_analysis)
        _write_metric_csv(slippage_path, "metric", report.slippage_report)
        parameters_path.write_text(
            json.dumps(report.parameter_snapshot, sort_keys=True, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        paths = [
            str(report_path),
            str(trades_path),
            str(equity_path),
            str(drawdown_path),
            str(returns_path),
            str(metrics_path),
            str(scenario_path),
            str(score_path),
            str(false_breakout_path),
            str(slippage_path),
            str(parameters_path),
        ]
        return report.model_copy(update={"artifact_paths": paths})

    def _evaluate_closed_bar(
        self,
        history: Sequence[Bar],
        current: Bar,
        next_bar: Bar,
        index: int,
        config_hash: str,
    ) -> BacktestTrade | None:
        levels = self.level_engine.detect_pivots(list(history), as_of_index=len(history) - 1)
        pivot_highs = [level for level in levels if level.price < current["close"]]
        if not pivot_highs:
            return None
        level = pivot_highs[-1]
        features = self.setup_evaluator.calculate_features(list(history), side=Side.LONG)
        score = self.setup_evaluator.score(features, side=Side.LONG)
        stop_price = current["close"] - self.config.stop_distance
        market = MarketSnapshot(
            symbol=current["symbol"],
            timestamp=current["ts"],
            price=current["close"],
            close=current["close"],
            high=current["high"],
            low=current["low"],
            bars_since_breakout=0,
            micro_impulse=current["close"] > current["open"],
        )
        intents = self.entry_engine.generate_intents(
            score=score,
            side=Side.LONG,
            level_price=level.price,
            base_quantity=self.config.base_quantity,
            stop_price=stop_price,
            market=market,
        )
        if not intents:
            return None
        intent = intents[-1]
        decision = self.risk_manager.evaluate(intent, RiskState())
        if not decision.approved or decision.quantity <= 0:
            return None
        return self._close_next_bar_trade(
            score=score,
            quantity=decision.quantity,
            current=current,
            next_bar=next_bar,
            index=index,
            config_hash=config_hash,
            level_price=level.price,
        )

    def _close_next_bar_trade(
        self,
        *,
        score: BreakoutScore,
        quantity: float,
        current: Bar,
        next_bar: Bar,
        index: int,
        config_hash: str,
        level_price: float,
    ) -> BacktestTrade:
        costs = self.config.cost_model
        entry_price = current["close"] + costs.spread / 2 + costs.slippage_per_unit
        exit_price = next_bar["close"] - costs.spread / 2 - costs.slippage_per_unit
        gross_pnl = (exit_price - entry_price) * quantity
        commission = costs.commission_per_unit * quantity * 2
        funding = costs.funding_per_bar * quantity
        total_cost = (
            commission + funding + costs.spread * quantity + costs.slippage_per_unit * quantity * 2
        )
        net_pnl = gross_pnl - total_cost
        trade_id = self._run_id(config_hash, f"{index}:{current['ts'].isoformat()}")[:16]
        return BacktestTrade(
            trade_id=trade_id,
            symbol=current["symbol"],
            side=Side.LONG,
            entry_time=current["ts"],
            exit_time=next_bar["ts"],
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            gross_pnl=gross_pnl,
            total_cost=total_cost,
            net_pnl=net_pnl,
            holding_bars=1,
            scenario=ScenarioType.CONSOLIDATION_BREAKOUT,
            score=score.total,
            slippage=costs.slippage_per_unit,
            metadata={"level_price": level_price, "index": index},
        )

    def _validation_windows(self, bar_count: int) -> list[BacktestWindow]:
        split = max(self.config.min_warmup_bars, bar_count // 2)
        return [
            BacktestWindow(name="in_sample", start_index=0, end_index=split, role="is"),
            BacktestWindow(
                name="out_of_sample", start_index=split, end_index=bar_count - 1, role="oos"
            ),
            BacktestWindow(name="walk_forward_train", start_index=0, end_index=split, role="train"),
            BacktestWindow(
                name="walk_forward_forward",
                start_index=split,
                end_index=bar_count - 1,
                role="forward",
            ),
        ]

    def _run_id(self, config_hash: str, dataset_hash: str) -> str:
        return stable_hash({"config_hash": config_hash, "dataset_hash": dataset_hash})[7:23]


def _write_csv_rows(
    path: Path,
    fieldnames: Sequence[str],
    rows: Sequence[Mapping[str, object]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_metric_csv(
    path: Path,
    key_name: str,
    values: Mapping[str, object],
    *,
    value_name: str = "value",
) -> None:
    rows = [
        {key_name: key, value_name: _normalize(value)}
        for key, value in sorted(values.items(), key=lambda item: item[0])
    ]
    _write_csv_rows(path, [key_name, value_name], rows)


def build_report(
    *,
    run_id: str,
    config_hash: str,
    dataset_hash: str,
    config: BacktestConfig,
    bars: Sequence[Bar],
    trades: Sequence[BacktestTrade],
    equity_curve: list[dict[str, float | str]],
    windows: Sequence[BacktestWindow],
    monte_carlo: MonteCarloResult,
    unavailable_reasons: Mapping[str, str] | None = None,
) -> BacktestReport:
    """Build metrics and diagnostic payloads from simulated trades."""

    metrics, metric_unavailable = _metrics(config.initial_equity, equity_curve, trades)
    unavailable = dict(metric_unavailable)
    unavailable.update(unavailable_reasons or {})
    scenario_breakdown: dict[str, int] = {}
    score_distribution: dict[str, int] = {}
    false_breakouts = 0
    for trade in trades:
        scenario_breakdown[trade.scenario.value] = (
            scenario_breakdown.get(trade.scenario.value, 0) + 1
        )
        bucket = f"{trade.score // 10 * 10}-{trade.score // 10 * 10 + 9}"
        score_distribution[bucket] = score_distribution.get(bucket, 0) + 1
        if trade.net_pnl < 0 and trade.exit_price < float(trade.metadata.get("level_price", 0.0)):
            false_breakouts += 1

    slippages = [trade.slippage for trade in trades]
    return BacktestReport(
        run_id=run_id,
        config_hash=config_hash,
        dataset_hash=dataset_hash,
        time_range=(bars[0]["ts"], bars[-1]["ts"]),
        parameter_snapshot=config.model_dump(mode="json"),
        metrics=metrics,
        unavailable_reasons=unavailable,
        equity_curve=equity_curve,
        drawdown_curve=_drawdown_curve(equity_curve),
        return_distribution=[trade.net_pnl / config.initial_equity for trade in trades],
        trades=list(trades),
        scenario_breakdown=scenario_breakdown,
        score_distribution=score_distribution,
        false_breakout_analysis={"count": false_breakouts},
        slippage_report={
            "average": sum(slippages) / len(slippages) if slippages else 0.0,
            "configured_per_unit": config.cost_model.slippage_per_unit,
        },
        windows=list(windows),
        monte_carlo=monte_carlo,
    )


def stable_hash(value: Any) -> str:
    """Return canonical sha256 hash for configs, datasets, and report inputs."""

    canonical = json.dumps(
        _normalize(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


OosGateReason = Literal[
    "approved",
    "missing_oos_thresholds",
    "oos_metric_missing",
    "oos_metric_unavailable",
    "oos_threshold_failed",
]
OosMetricName = Literal[
    "oos_performance",
    "max_drawdown",
    "win_rate",
    "profit_factor",
    "trade_count",
]


def evaluate_production_oos_gate(
    report: BacktestReport,
    thresholds: ProductionOosThresholds,
) -> ProductionOosGateDecision:
    """Evaluate a completed report against explicit local OOS approval thresholds."""

    if not thresholds.configured:
        return ProductionOosGateDecision(
            approved=False,
            reason="missing_oos_thresholds",
            blockers=["missing_oos_thresholds"],
        )

    blockers: list[str] = []
    checked: list[ProductionOosMetricCheck] = []
    threshold_map: list[tuple[OosMetricName, float | int | None]] = [
        ("oos_performance", thresholds.min_oos_performance),
        ("max_drawdown", thresholds.max_drawdown_floor),
        ("win_rate", thresholds.min_win_rate),
        ("profit_factor", thresholds.min_profit_factor),
        ("trade_count", thresholds.min_trade_count),
    ]

    for metric, threshold in threshold_map:
        if threshold is None:
            continue
        if metric in report.unavailable_reasons:
            blockers.append(f"{metric}_unavailable")
            continue
        value = report.metrics.get(metric)
        if not isinstance(value, int | float) or value is None:
            blockers.append(f"{metric}_missing")
            continue
        passed = float(value) >= float(threshold)
        checked.append(
            ProductionOosMetricCheck(
                metric=metric,
                actual=float(value),
                threshold=float(threshold),
                passed=passed,
            )
        )
        if not passed:
            blockers.append(f"{metric}_below_threshold")

    if blockers:
        return ProductionOosGateDecision(
            approved=False,
            reason=_oos_block_reason(blockers),
            checked_metrics=checked,
            blockers=blockers,
        )
    return ProductionOosGateDecision(approved=True, reason="approved", checked_metrics=checked)


def _oos_block_reason(blockers: Sequence[str]) -> OosGateReason:
    if any(blocker.endswith("_unavailable") for blocker in blockers):
        return "oos_metric_unavailable"
    if any(blocker.endswith("_missing") for blocker in blockers):
        return "oos_metric_missing"
    return cast(OosGateReason, "oos_threshold_failed")


def _metrics(
    initial_equity: float,
    equity_curve: Sequence[Mapping[str, float | str]],
    trades: Sequence[BacktestTrade],
) -> tuple[dict[str, float | int | str | None], dict[str, str]]:
    final_equity = float(equity_curve[-1]["equity"])
    net_profit = final_equity - initial_equity
    wins = [trade for trade in trades if trade.net_pnl > 0]
    losses = [trade for trade in trades if trade.net_pnl < 0]
    returns = [trade.net_pnl / initial_equity for trade in trades]
    unavailable: dict[str, str] = {}
    if len(returns) < 2:
        unavailable["sharpe_ratio"] = "at least two trades are required"
    sharpe = _sharpe(returns) if len(returns) >= 2 else None
    profit_factor = (
        sum(trade.net_pnl for trade in wins) / abs(sum(trade.net_pnl for trade in losses))
        if losses
        else None
    )
    if profit_factor is None:
        unavailable["profit_factor"] = "no losing trades in sample"
    return {
        "net_profit": net_profit,
        "cagr": net_profit / initial_equity,
        "sharpe_ratio": sharpe,
        "max_drawdown": min(point["drawdown"] for point in _drawdown_curve(equity_curve)),
        "win_rate": len(wins) / len(trades) if trades else 0.0,
        "expectancy": sum(trade.net_pnl for trade in trades) / len(trades) if trades else 0.0,
        "average_trade": sum(trade.net_pnl for trade in trades) / len(trades) if trades else 0.0,
        "avg_holding_time": sum(trade.holding_bars for trade in trades) / len(trades)
        if trades
        else 0.0,
        "oos_performance": net_profit,
        "profit_factor": profit_factor,
        "exposure": len(trades) / max(len(equity_curve), 1),
        "trade_count": len(trades),
    }, unavailable


def _sharpe(returns: Sequence[float]) -> float | None:
    average = sum(returns) / len(returns)
    variance = sum((value - average) ** 2 for value in returns) / (len(returns) - 1)
    if variance <= 0:
        return None
    return average / variance**0.5


def _drawdown_curve(
    equity_curve: Sequence[Mapping[str, float | str]],
) -> list[dict[str, float | str]]:
    peak = float(equity_curve[0]["equity"])
    drawdowns: list[dict[str, float | str]] = []
    for point in equity_curve:
        equity = float(point["equity"])
        peak = max(peak, equity)
        drawdown = (equity - peak) / peak if peak else 0.0
        drawdowns.append({"timestamp": str(point["timestamp"]), "drawdown": drawdown})
    return drawdowns


def _normalize(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _normalize(value.model_dump(mode="json"))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _normalize(value[key]) for key in sorted(value)}
    if isinstance(value, tuple | list):
        return [_normalize(item) for item in value]
    return value
