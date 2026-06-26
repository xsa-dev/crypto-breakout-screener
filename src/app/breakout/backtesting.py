"""Deterministic local backtesting and report exports for breakout research."""

import csv
import hashlib
import json
import random
from bisect import bisect_right
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
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


@dataclass
class ResearchGateState:
    """Mutable local state for disabled-by-default research entry gates."""

    last_exit_time: datetime | None = None
    last_exit_index: int | None = None
    last_trade_net_pnl: float | None = None
    cooldown_until_index: int = -1
    trades_by_day: dict[str, int] = field(default_factory=dict)
    pnl_by_day: dict[str, float] = field(default_factory=dict)
    skip_counts: Counter[str] = field(default_factory=Counter)


class BacktestEngine:
    """Closed-bar deterministic replay engine with no live broker side effects."""

    def __init__(
        self,
        config: BacktestConfig | None = None,
        *,
        context_bars: Mapping[str, Sequence[Bar]] | None = None,
    ) -> None:
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
        self.context_bars = {
            timeframe: sorted(bars, key=lambda bar: bar["ts"])
            for timeframe, bars in (context_bars or {}).items()
        }
        self.context_close_timestamps = {
            timeframe: [_bar_close_time(bar) for bar in bars]
            for timeframe, bars in self.context_bars.items()
        }

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
        gate_state = ResearchGateState()

        for index in range(self.config.min_warmup_bars, len(ordered) - 1):
            history = ordered[: index + 1]
            current = ordered[index]
            next_bar = ordered[index + 1]
            trade = self._evaluate_closed_bar(
                history,
                current,
                next_bar,
                index,
                config_hash,
                gate_state,
            )
            if trade is None:
                equity_curve.append({"timestamp": current["ts"].isoformat(), "equity": equity})
                continue
            trades.append(trade)
            self._update_gate_state(gate_state, trade=trade, index=index)
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
            gate_skip_counts=dict(gate_state.skip_counts),
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
        daily_summary_path = directory / f"{report.run_id}-daily-summary.csv"
        weekly_summary_path = directory / f"{report.run_id}-weekly-summary.csv"
        lifecycle_path = directory / f"{report.run_id}-lifecycle-diagnostics.csv"
        score_bucket_pnl_path = directory / f"{report.run_id}-score-bucket-pnl.csv"
        entry_features_path = directory / f"{report.run_id}-entry-feature-snapshots.csv"
        feature_bucket_pnl_path = directory / f"{report.run_id}-feature-bucket-pnl.csv"
        regime_bucket_path = directory / f"{report.run_id}-regime-bucket-summary.csv"
        worst_day_path = directory / f"{report.run_id}-worst-day-attribution.csv"
        parameters_path = directory / f"{report.run_id}-parameters.json"

        report_path.write_text(
            json.dumps(
                _normalize(_report_without_feature_metadata(report)),
                sort_keys=True,
                indent=2,
                ensure_ascii=False,
            ),
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
        _write_csv_rows(
            daily_summary_path,
            [
                "day",
                "trade_count",
                "net_pnl",
                "gross_pnl",
                "total_cost",
                "win_count",
                "loss_count",
                "win_rate",
                "max_loss_streak_inside_period",
            ],
            daily_trade_summary(report.trades),
        )
        _write_csv_rows(
            weekly_summary_path,
            [
                "week",
                "trade_count",
                "net_pnl",
                "gross_pnl",
                "total_cost",
                "win_count",
                "loss_count",
                "win_rate",
                "max_loss_streak_inside_period",
            ],
            weekly_trade_summary(report.trades),
        )
        _write_metric_csv(lifecycle_path, "metric", lifecycle_diagnostics(report))
        _write_csv_rows(
            score_bucket_pnl_path,
            ["score", "trade_count", "net_pnl", "average_trade", "win_rate"],
            score_bucket_pnl(report.trades),
        )
        _write_dynamic_csv_rows(entry_features_path, entry_feature_snapshots(report.trades))
        _write_csv_rows(
            feature_bucket_pnl_path,
            ["feature", "bucket", "trade_count", "net_pnl", "average_trade", "win_rate", "profit_factor"],
            feature_bucket_pnl(report.trades),
        )
        _write_csv_rows(
            regime_bucket_path,
            ["regime", "trade_count", "net_pnl", "average_trade", "win_rate", "profit_factor"],
            regime_bucket_summary(report.trades),
        )
        _write_csv_rows(
            worst_day_path,
            ["day", "trade_count", "net_pnl", "dominant_atr_bucket", "dominant_candle_body_bucket", "context_available"],
            worst_day_attribution(report.trades),
        )
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
            str(daily_summary_path),
            str(weekly_summary_path),
            str(lifecycle_path),
            str(score_bucket_pnl_path),
            str(entry_features_path),
            str(feature_bucket_pnl_path),
            str(regime_bucket_path),
            str(worst_day_path),
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
        gate_state: ResearchGateState,
    ) -> BacktestTrade | None:
        levels = self.level_engine.detect_pivots(list(history), as_of_index=len(history) - 1)
        pivot_highs = [level for level in levels if level.price < current["close"]]
        if not pivot_highs:
            return None
        level = pivot_highs[-1]
        features = self.setup_evaluator.calculate_features(list(history), side=Side.LONG)
        score = self.setup_evaluator.score(features, side=Side.LONG)
        feature_snapshot = self._entry_feature_snapshot(
            history=history,
            current=current,
            index=index,
            level_price=level.price,
            features=features,
            score=score,
            gate_state=gate_state,
        )
        score_blocker = self._research_gate_reason(
            gate_state,
            current=current,
            index=index,
            score=score.total,
        )
        if score_blocker is not None:
            gate_state.skip_counts[score_blocker] += 1
            return None
        feature_blocker = self._feature_filter_reason(feature_snapshot)
        if feature_blocker is not None:
            gate_state.skip_counts[feature_blocker] += 1
            return None
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
            feature_snapshot=feature_snapshot,
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
        feature_snapshot: Mapping[str, float | int | str | bool],
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
            metadata={"level_price": level_price, "index": index, **dict(feature_snapshot)},
        )

    def _entry_feature_snapshot(
        self,
        *,
        history: Sequence[Bar],
        current: Bar,
        index: int,
        level_price: float,
        features: Any,
        score: Any,
        gate_state: ResearchGateState,
    ) -> dict[str, float | int | str | bool]:
        atr = _safe_positive_float(getattr(features, "atr", None))
        current_range = max(current["high"] - current["low"], 1e-9)
        body = abs(current["close"] - current["open"])
        day_key = current["ts"].date().isoformat()
        snapshot: dict[str, float | int | str | bool] = {
            "feature_entry_index": index,
            "feature_setup_score_total": int(getattr(score, "total", 0)),
            "feature_score_eligibility": str(getattr(score, "eligibility", "unknown")),
            "feature_score_consolidation": int(getattr(score, "consolidation", 0)),
            "feature_score_slow_approach": int(getattr(score, "slow_approach", 0)),
            "feature_score_trend": int(getattr(score, "trend", 0)),
            "feature_score_activity": int(getattr(score, "activity", 0)),
            "feature_score_density": int(getattr(score, "density", 0)),
            "feature_atr": atr if atr is not None else "unavailable",
            "feature_atr_percentile": _atr_percentile(history, atr),
            "feature_candle_body_range_ratio": body / current_range,
            "feature_close_position_in_range": (current["close"] - current["low"]) / current_range,
            "feature_breakout_distance_atr": _ratio_or_unavailable(current["close"] - level_price, atr),
            "feature_consolidation_range_atr": _value_or_unavailable(getattr(features, "consolidation_range_atr", None)),
            "feature_approach_velocity": _value_or_unavailable(getattr(features, "approach_velocity", None)),
            "feature_activity_ratio": _value_or_unavailable(getattr(features, "activity_ratio", None)),
            "feature_ema_fast_distance_atr": _ratio_or_unavailable(current["close"] - getattr(features, "ema_fast", 0.0), atr)
            if getattr(features, "ema_fast", None) is not None
            else "unavailable",
            "feature_ema_slow_distance_atr": _ratio_or_unavailable(current["close"] - getattr(features, "ema_slow", 0.0), atr)
            if getattr(features, "ema_slow", None) is not None
            else "unavailable",
            "feature_ema_slope_atr": _ema_slope_atr(history, atr),
            "feature_recent_range_compression": _recent_range_compression(history, atr),
            "feature_recent_high_distance_atr": _recent_extreme_distance_atr(history, atr, high=True),
            "feature_recent_low_distance_atr": _recent_extreme_distance_atr(history, atr, high=False),
            "feature_volume_ratio": _volume_ratio(history),
            "feature_trades_today_before_entry": gate_state.trades_by_day.get(day_key, 0),
            "feature_realized_pnl_today_before_entry": gate_state.pnl_by_day.get(day_key, 0.0),
            "feature_bars_since_previous_exit": index - gate_state.last_exit_index
            if gate_state.last_exit_index is not None
            else "unavailable",
            "feature_previous_trade_was_loss": bool(
                gate_state.last_trade_net_pnl is not None and gate_state.last_trade_net_pnl < 0
            ),
        }
        snapshot.update(
            _context_feature_snapshot(
                self.context_bars,
                self.context_close_timestamps,
                current["ts"],
            )
        )
        return snapshot

    def _research_gate_reason(
        self,
        gate_state: ResearchGateState,
        *,
        current: Bar,
        index: int,
        score: int,
    ) -> str | None:
        gates = self.config.research_gates
        if gates.min_entry_score is not None and score < gates.min_entry_score:
            return "skipped_min_entry_score"
        if index <= gate_state.cooldown_until_index:
            return "skipped_cooldown"
        if gates.block_immediate_reentry and gate_state.last_exit_time == current["ts"]:
            return "skipped_immediate_reentry"
        day_key = current["ts"].date().isoformat()
        if gates.max_trades_per_day is not None:
            if gate_state.trades_by_day.get(day_key, 0) >= gates.max_trades_per_day:
                return "skipped_max_trades_per_day"
        if gates.daily_stop_loss is not None:
            if gate_state.pnl_by_day.get(day_key, 0.0) <= -gates.daily_stop_loss:
                return "skipped_daily_stop_loss"
        return None

    def _feature_filter_reason(
        self,
        feature_snapshot: Mapping[str, float | int | str | bool],
    ) -> str | None:
        filters = self.config.feature_filters
        if filters.require_m15_ema_slope_positive:
            slope = feature_snapshot.get("feature_ema_slope_atr")
            if not isinstance(slope, int | float) or slope <= 0:
                return "skipped_feature_m15_ema_slope_not_positive"
        if filters.require_h1_trend_long:
            if feature_snapshot.get("feature_context_H1_trend_alignment") != "long":
                return "skipped_feature_h1_trend_not_long"
        if filters.min_atr_percentile is not None:
            atr_percentile = feature_snapshot.get("feature_atr_percentile")
            if not isinstance(atr_percentile, int | float):
                return "skipped_feature_atr_percentile_unavailable"
            if atr_percentile <= filters.min_atr_percentile:
                return "skipped_feature_atr_percentile_below_min"
        if filters.max_breakout_distance_atr is not None:
            breakout_distance = feature_snapshot.get("feature_breakout_distance_atr")
            if not isinstance(breakout_distance, int | float):
                return "skipped_feature_breakout_distance_atr_unavailable"
            if breakout_distance > filters.max_breakout_distance_atr:
                return "skipped_feature_breakout_distance_atr_above_cap"
        if filters.min_candle_body_ratio is not None:
            body_ratio = feature_snapshot.get("feature_candle_body_range_ratio")
            if not isinstance(body_ratio, int | float):
                return "skipped_feature_candle_body_ratio_unavailable"
            if body_ratio <= filters.min_candle_body_ratio:
                return "skipped_feature_candle_body_ratio_below_min"
        if filters.max_candle_body_ratio is not None:
            body_ratio = feature_snapshot.get("feature_candle_body_range_ratio")
            if not isinstance(body_ratio, int | float):
                return "skipped_feature_candle_body_ratio_unavailable"
            if body_ratio > filters.max_candle_body_ratio:
                return "skipped_feature_candle_body_ratio_above_cap"
        return None

    def _update_gate_state(
        self,
        gate_state: ResearchGateState,
        *,
        trade: BacktestTrade,
        index: int,
    ) -> None:
        gates = self.config.research_gates
        day_key = trade.exit_time.date().isoformat()
        gate_state.trades_by_day[day_key] = gate_state.trades_by_day.get(day_key, 0) + 1
        gate_state.pnl_by_day[day_key] = gate_state.pnl_by_day.get(day_key, 0.0) + trade.net_pnl
        gate_state.last_exit_time = trade.exit_time
        gate_state.last_exit_index = index + trade.holding_bars
        gate_state.last_trade_net_pnl = trade.net_pnl
        cooldown = gates.cooldown_bars_after_trade
        if trade.net_pnl < 0:
            cooldown = max(cooldown, gates.cooldown_bars_after_loss)
        if cooldown > 0:
            gate_state.cooldown_until_index = max(gate_state.cooldown_until_index, index + cooldown)

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


def _write_dynamic_csv_rows(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    base_fields = [
        "trade_id",
        "symbol",
        "side",
        "entry_time",
        "entry_index",
        "score",
        "net_pnl",
        "gross_pnl",
        "total_cost",
    ]
    dynamic_fields = sorted({key for row in rows for key in row if key not in base_fields})
    _write_csv_rows(path, [*base_fields, *dynamic_fields], rows)


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


def daily_trade_summary(trades: Sequence[BacktestTrade]) -> list[dict[str, object]]:
    """Return deterministic per-UTC-day trade grouping diagnostics."""

    return _period_trade_summary(trades, period="day")


def weekly_trade_summary(trades: Sequence[BacktestTrade]) -> list[dict[str, object]]:
    """Return deterministic per-ISO-week trade grouping diagnostics."""

    return _period_trade_summary(trades, period="week")


def lifecycle_diagnostics(report: BacktestReport) -> dict[str, object]:
    """Summarize lifecycle/overtrading diagnostics for a completed report."""

    trades = report.trades
    holding_values = [trade.holding_bars for trade in trades]
    daily_counts = Counter(trade.entry_time.date().isoformat() for trade in trades)
    immediate_reentries = 0
    previous_exit: datetime | None = None
    for trade in trades:
        if previous_exit is not None and trade.entry_time == previous_exit:
            immediate_reentries += 1
        previous_exit = trade.exit_time
    side_distribution = Counter(trade.side.value for trade in trades)
    holding_distribution = Counter(holding_values)
    scores = [trade.score for trade in trades]
    total_bars = report.metrics.get("bar_count")
    bar_count = int(total_bars) if isinstance(total_bars, int | float) else None
    diagnostics: dict[str, object] = {
        "total_trades": len(trades),
        "total_bars": bar_count if bar_count is not None else "unavailable",
        "trades_per_bar": len(trades) / bar_count if bar_count else None,
        "holding_bars_min": min(holding_values) if holding_values else 0,
        "holding_bars_max": max(holding_values) if holding_values else 0,
        "holding_bars_average": sum(holding_values) / len(holding_values) if holding_values else 0.0,
        "holding_bars_distribution": _counter_string(holding_distribution),
        "immediate_reentry_count": immediate_reentries,
        "immediate_reentry_ratio": immediate_reentries / max(len(trades) - 1, 1) if trades else 0.0,
        "same_day_max_trades": max(daily_counts.values()) if daily_counts else 0,
        "average_daily_trades": sum(daily_counts.values()) / len(daily_counts) if daily_counts else 0.0,
        "max_losing_streak": _max_losing_streak(trades),
        "side_distribution": _counter_string(side_distribution),
        "entry_score_min": min(scores) if scores else 0,
        "entry_score_max": max(scores) if scores else 0,
        "entry_score_average": sum(scores) / len(scores) if scores else 0.0,
        "repeated_level_trade_count": _repeated_level_trade_count(trades),
    }
    skip_counts = report.parameter_snapshot.get("research_gate_skip_counts", {})
    if isinstance(skip_counts, Mapping):
        for key, value in sorted(skip_counts.items()):
            diagnostics[f"gate_{key}"] = value
    return diagnostics


def score_bucket_pnl(trades: Sequence[BacktestTrade]) -> list[dict[str, object]]:
    """Return PnL grouped by exact score for score-quality diagnostics."""

    grouped: dict[int, list[BacktestTrade]] = defaultdict(list)
    for trade in trades:
        grouped[trade.score].append(trade)
    rows: list[dict[str, object]] = []
    for score in sorted(grouped):
        score_trades = grouped[score]
        net_pnl = sum(trade.net_pnl for trade in score_trades)
        wins = sum(1 for trade in score_trades if trade.net_pnl > 0)
        rows.append(
            {
                "score": score,
                "trade_count": len(score_trades),
                "net_pnl": net_pnl,
                "average_trade": net_pnl / len(score_trades),
                "win_rate": wins / len(score_trades),
            }
        )
    return rows


def entry_feature_snapshots(trades: Sequence[BacktestTrade]) -> list[dict[str, object]]:
    """Return one deterministic feature row per completed trade."""

    rows: list[dict[str, object]] = []
    for trade in trades:
        feature_values = {
            key: value for key, value in trade.metadata.items() if key.startswith("feature_")
        }
        rows.append(
            {
                "trade_id": trade.trade_id,
                "symbol": trade.symbol,
                "side": trade.side.value,
                "entry_time": trade.entry_time.isoformat(),
                "entry_index": trade.metadata.get("index", "unavailable"),
                "score": trade.score,
                "net_pnl": trade.net_pnl,
                "gross_pnl": trade.gross_pnl,
                "total_cost": trade.total_cost,
                **feature_values,
            }
        )
    return rows


def feature_bucket_pnl(trades: Sequence[BacktestTrade]) -> list[dict[str, object]]:
    """Return PnL grouped by high-signal diagnostic feature buckets."""

    bucket_extractors = {
        "atr_percentile": lambda trade: _numeric_bucket(
            trade.metadata.get("feature_atr_percentile"), [0.25, 0.5, 0.75]
        ),
        "candle_body_ratio": lambda trade: _numeric_bucket(
            trade.metadata.get("feature_candle_body_range_ratio"), [0.25, 0.5, 0.75]
        ),
        "breakout_distance_atr": lambda trade: _numeric_bucket(
            trade.metadata.get("feature_breakout_distance_atr"), [0.25, 0.5, 1.0]
        ),
        "m15_ema_slope": lambda trade: _direction_bucket(
            trade.metadata.get("feature_ema_slope_atr")
        ),
        "h1_trend_alignment": lambda trade: str(
            trade.metadata.get("feature_context_H1_trend_alignment", "unavailable")
        ),
        "h4_trend_alignment": lambda trade: str(
            trade.metadata.get("feature_context_H4_trend_alignment", "unavailable")
        ),
        "d1_trend_alignment": lambda trade: str(
            trade.metadata.get("feature_context_D1_trend_alignment", "unavailable")
        ),
    }
    rows: list[dict[str, object]] = []
    for feature, extractor in bucket_extractors.items():
        grouped: dict[str, list[BacktestTrade]] = defaultdict(list)
        for trade in trades:
            grouped[extractor(trade)].append(trade)
        for bucket in sorted(grouped):
            rows.append({"feature": feature, "bucket": bucket, **_trade_group_metrics(grouped[bucket])})
    return rows


def regime_bucket_summary(trades: Sequence[BacktestTrade]) -> list[dict[str, object]]:
    """Return coarser combined-regime buckets for quick research triage."""

    grouped: dict[str, list[BacktestTrade]] = defaultdict(list)
    for trade in trades:
        atr_bucket = _numeric_bucket(trade.metadata.get("feature_atr_percentile"), [0.25, 0.5, 0.75])
        candle_bucket = _numeric_bucket(
            trade.metadata.get("feature_candle_body_range_ratio"), [0.25, 0.5, 0.75]
        )
        h1 = trade.metadata.get("feature_context_H1_trend_alignment", "unavailable")
        regime = f"atr={atr_bucket}|body={candle_bucket}|h1={h1}"
        grouped[regime].append(trade)
    return [
        {"regime": regime, **_trade_group_metrics(regime_trades)}
        for regime, regime_trades in sorted(grouped.items())
    ]


def worst_day_attribution(trades: Sequence[BacktestTrade]) -> list[dict[str, object]]:
    """Return days with realized net losses and dominant diagnostic buckets."""

    grouped: dict[str, list[BacktestTrade]] = defaultdict(list)
    for trade in trades:
        grouped[trade.exit_time.date().isoformat()].append(trade)
    rows: list[dict[str, object]] = []
    for day, day_trades in sorted(grouped.items()):
        net_pnl = sum(trade.net_pnl for trade in day_trades)
        if net_pnl >= 0:
            continue
        atr_buckets = Counter(
            _numeric_bucket(trade.metadata.get("feature_atr_percentile"), [0.25, 0.5, 0.75])
            for trade in day_trades
        )
        candle_buckets = Counter(
            _numeric_bucket(
                trade.metadata.get("feature_candle_body_range_ratio"), [0.25, 0.5, 0.75]
            )
            for trade in day_trades
        )
        context_available = any(
            bool(trade.metadata.get("feature_context_H1_available", False)) for trade in day_trades
        )
        rows.append(
            {
                "day": day,
                "trade_count": len(day_trades),
                "net_pnl": net_pnl,
                "dominant_atr_bucket": atr_buckets.most_common(1)[0][0],
                "dominant_candle_body_bucket": candle_buckets.most_common(1)[0][0],
                "context_available": context_available,
            }
        )
    return sorted(rows, key=lambda row: row["net_pnl"] if isinstance(row["net_pnl"], int | float) else 0.0)


def _period_trade_summary(
    trades: Sequence[BacktestTrade],
    *,
    period: Literal["day", "week"],
) -> list[dict[str, object]]:
    grouped: dict[str, list[BacktestTrade]] = defaultdict(list)
    for trade in trades:
        if period == "day":
            key = trade.entry_time.date().isoformat()
        else:
            calendar = trade.entry_time.isocalendar()
            key = f"{calendar.year}-W{calendar.week:02d}"
        grouped[key].append(trade)
    rows: list[dict[str, object]] = []
    key_name = "day" if period == "day" else "week"
    for key in sorted(grouped):
        period_trades = grouped[key]
        wins = [trade for trade in period_trades if trade.net_pnl > 0]
        losses = [trade for trade in period_trades if trade.net_pnl < 0]
        rows.append(
            {
                key_name: key,
                "trade_count": len(period_trades),
                "net_pnl": sum(trade.net_pnl for trade in period_trades),
                "gross_pnl": sum(trade.gross_pnl for trade in period_trades),
                "total_cost": sum(trade.total_cost for trade in period_trades),
                "win_count": len(wins),
                "loss_count": len(losses),
                "win_rate": len(wins) / len(period_trades),
                "max_loss_streak_inside_period": _max_losing_streak(period_trades),
            }
        )
    return rows


def _max_losing_streak(trades: Sequence[BacktestTrade]) -> int:
    current = 0
    maximum = 0
    for trade in trades:
        if trade.net_pnl < 0:
            current += 1
            maximum = max(maximum, current)
        else:
            current = 0
    return maximum


def _repeated_level_trade_count(trades: Sequence[BacktestTrade]) -> int:
    seen: set[str] = set()
    repeated = 0
    for trade in trades:
        level_price = trade.metadata.get("level_price")
        if level_price is None:
            continue
        key = f"{trade.symbol}:{trade.side.value}:{float(level_price):.8f}"
        if key in seen:
            repeated += 1
        seen.add(key)
    return repeated


def _counter_string(counter: Counter[Any]) -> str:
    return ";".join(f"{key}:{counter[key]}" for key in sorted(counter, key=str))


def _trade_group_metrics(trades: Sequence[BacktestTrade]) -> dict[str, object]:
    net_pnl = sum(trade.net_pnl for trade in trades)
    wins = sum(1 for trade in trades if trade.net_pnl > 0)
    gross_profit = sum(trade.net_pnl for trade in trades if trade.net_pnl > 0)
    gross_loss = abs(sum(trade.net_pnl for trade in trades if trade.net_pnl < 0))
    return {
        "trade_count": len(trades),
        "net_pnl": net_pnl,
        "average_trade": net_pnl / len(trades) if trades else 0.0,
        "win_rate": wins / len(trades) if trades else 0.0,
        "profit_factor": gross_profit / gross_loss if gross_loss > 0 else "unavailable",
    }


def _numeric_bucket(value: object, cuts: Sequence[float]) -> str:
    if not isinstance(value, int | float):
        return "unavailable"
    lower = "-inf"
    for cut in cuts:
        if float(value) <= cut:
            return f"{lower}..{cut}"
        lower = str(cut)
    return f">{cuts[-1]}" if cuts else "available"


def _direction_bucket(value: object) -> str:
    if not isinstance(value, int | float):
        return "unavailable"
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "flat"


def _safe_positive_float(value: object) -> float | None:
    if not isinstance(value, int | float):
        return None
    numeric = float(value)
    return numeric if numeric > 0 else None


def _value_or_unavailable(value: object) -> float | int | str:
    return value if isinstance(value, int | float) else "unavailable"


def _ratio_or_unavailable(numerator: float, denominator: float | None) -> float | str:
    return numerator / denominator if denominator else "unavailable"


def _true_range(bar: Bar, previous_close: float | None = None) -> float:
    true_range = bar["high"] - bar["low"]
    if previous_close is not None:
        true_range = max(true_range, abs(bar["high"] - previous_close), abs(bar["low"] - previous_close))
    return true_range


def _atr_from_bars(bars: Sequence[Bar], period: int = 14) -> float | None:
    if not bars:
        return None
    ranges: list[float] = []
    previous_close: float | None = None
    for bar in bars[-period:]:
        ranges.append(_true_range(bar, previous_close))
        previous_close = bar["close"]
    return sum(ranges) / len(ranges) if ranges else None


def _atr_percentile(
    history: Sequence[Bar],
    current_atr: float | None,
    *,
    atr_period: int = 14,
    rank_window: int = 100,
) -> float | str:
    if current_atr is None or len(history) < atr_period:
        return "unavailable"
    sample = history[-(rank_window + atr_period) :]
    true_ranges: list[float] = []
    previous_close: float | None = None
    for bar in sample:
        true_ranges.append(_true_range(bar, previous_close))
        previous_close = bar["close"]
    atr_values = [
        sum(true_ranges[index - atr_period : index]) / atr_period
        for index in range(atr_period, len(true_ranges) + 1)
    ]
    if not atr_values:
        return "unavailable"
    return sum(1 for value in atr_values if value <= current_atr) / len(atr_values)


def _ema(values: Sequence[float], period: int) -> float | None:
    if not values:
        return None
    smoothing = 2 / (period + 1)
    ema = values[0]
    for value in values[1:]:
        ema = value * smoothing + ema * (1 - smoothing)
    return ema


def _ema_slope_atr(history: Sequence[Bar], atr: float | None, period: int = 20, lag: int = 5) -> float | str:
    if atr is None or len(history) <= lag:
        return "unavailable"
    closes = [bar["close"] for bar in history]
    current = _ema(closes, period)
    previous = _ema(closes[:-lag], period)
    if current is None or previous is None:
        return "unavailable"
    return (current - previous) / atr


def _recent_range_compression(history: Sequence[Bar], atr: float | None, lookback: int = 20) -> float | str:
    if atr is None or not history:
        return "unavailable"
    recent = history[-lookback:]
    span = max(bar["high"] for bar in recent) - min(bar["low"] for bar in recent)
    return span / atr


def _recent_extreme_distance_atr(
    history: Sequence[Bar], atr: float | None, *, high: bool, lookback: int = 20
) -> float | str:
    if atr is None or not history:
        return "unavailable"
    recent = history[-lookback:]
    current_close = history[-1]["close"]
    extreme = max(bar["high"] for bar in recent) if high else min(bar["low"] for bar in recent)
    return (current_close - extreme) / atr


def _volume_ratio(history: Sequence[Bar], lookback: int = 20) -> float | str:
    if len(history) < 2:
        return "unavailable"
    recent = history[-lookback - 1 : -1]
    average = sum(bar["volume"] for bar in recent) / len(recent) if recent else 0.0
    return history[-1]["volume"] / average if average > 0 else "unavailable"


def _timeframe_seconds(timeframe: str) -> int:
    mapping = {
        "M1": 60,
        "M5": 300,
        "M15": 900,
        "M30": 1800,
        "H1": 3600,
        "H4": 14400,
        "D1": 86400,
        "1": 60,
        "5": 300,
        "15": 900,
        "30": 1800,
        "60": 3600,
        "240": 14400,
        "D": 86400,
    }
    return mapping.get(timeframe.upper(), 0)


def _bar_close_time(bar: Bar) -> datetime:
    return bar["ts"] + timedelta(seconds=_timeframe_seconds(bar["timeframe"]))


def _context_feature_snapshot(
    context_bars: Mapping[str, Sequence[Bar]],
    context_timestamps: Mapping[str, Sequence[datetime]],
    entry_time: datetime,
) -> dict[str, float | int | str | bool]:
    result: dict[str, float | int | str | bool] = {}
    for timeframe in ("H1", "H4", "D1"):
        prefix = f"feature_context_{timeframe}"
        bars = context_bars.get(timeframe, ())
        timestamps = context_timestamps.get(timeframe, ())
        closed_end = bisect_right(timestamps, entry_time)
        closed = bars[max(0, closed_end - 250) : closed_end]
        if not closed:
            result[f"{prefix}_available"] = False
            result[f"{prefix}_reason"] = "not_supplied_or_no_closed_bar"
            result[f"{prefix}_trend_alignment"] = "unavailable"
            continue
        closes = [bar["close"] for bar in closed]
        ema_fast = _ema(closes, 50)
        ema_slow = _ema(closes, 200)
        atr = _atr_from_bars(closed)
        slope = _ema_slope_atr(closed, atr)
        trend_alignment = "unavailable"
        if ema_fast is not None and ema_slow is not None:
            trend_alignment = "long" if ema_fast > ema_slow else "short_or_flat"
        result.update(
            {
                f"{prefix}_available": True,
                f"{prefix}_timestamp": closed[-1]["ts"].isoformat(),
                f"{prefix}_trend_alignment": trend_alignment,
                f"{prefix}_ema_fast_distance_atr": _ratio_or_unavailable(closed[-1]["close"] - ema_fast, atr)
                if ema_fast is not None
                else "unavailable",
                f"{prefix}_ema_slow_distance_atr": _ratio_or_unavailable(closed[-1]["close"] - ema_slow, atr)
                if ema_slow is not None
                else "unavailable",
                f"{prefix}_ema_slope_atr": slope,
                f"{prefix}_atr": atr if atr is not None else "unavailable",
            }
        )
    return result


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
    gate_skip_counts: Mapping[str, int] | None = None,
) -> BacktestReport:
    """Build metrics and diagnostic payloads from simulated trades."""

    metrics, metric_unavailable = _metrics(config.initial_equity, equity_curve, trades)
    metrics["bar_count"] = len(bars)
    unavailable = dict(metric_unavailable)
    unavailable.update(unavailable_reasons or {})
    parameter_snapshot = config.model_dump(mode="json")
    parameter_snapshot["research_gate_skip_counts"] = dict(sorted((gate_skip_counts or {}).items()))
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
        parameter_snapshot=parameter_snapshot,
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


def _report_without_feature_metadata(report: BacktestReport) -> BacktestReport:
    """Return a report copy with feature-heavy trade metadata stripped from JSON payload.

    Feature diagnostics are exported as dedicated CSV artifacts; the main report JSON keeps
    only compact non-feature metadata such as level price and entry index.
    """

    slim_trades = [
        trade.model_copy(
            update={
                "metadata": {
                    key: value
                    for key, value in trade.metadata.items()
                    if not key.startswith("feature_")
                }
            }
        )
        for trade in report.trades
    ]
    return report.model_copy(update={"trades": slim_trades})


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
