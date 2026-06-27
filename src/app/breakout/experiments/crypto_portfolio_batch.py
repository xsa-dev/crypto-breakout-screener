"""Shared-bankroll public crypto portfolio batch research runner."""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, Field

from src.app.breakout.experiments.crypto_batch import (
    BatchExperimentResult,
    BatchWindow,
    BatchWindowSummary,
    ResearchThresholds,
    fixed_altcoin_research_universe,
    parse_windows,
    preset_windows,
    run_batch_experiment,
)
from src.app.breakout.experiments.crypto_symbols import resolve_crypto_research_universe
from src.app.breakout.normalizer import to_utc

RunSymbolBatchCallable = Callable[..., BatchExperimentResult]


class PortfolioTrade(BaseModel):
    """Trade candidate used for shared-bankroll portfolio aggregation."""

    symbol: str
    window_label: str
    entry_time: datetime
    exit_time: datetime
    net_pnl: float
    quantity: float = 0.0
    entry_price: float = 0.0
    notional: float = 0.0
    accepted: bool = True
    blocker: str | None = None
    regime_label: Literal["bull_long", "bear_short_or_avoid", "neutral_blocked"] = "neutral_blocked"
    regime_decision: Literal["long_enabled", "risk_off_blocked"] = "risk_off_blocked"
    source_trade_id: str | None = None
    source_artifact_dir: str | None = None


class PortfolioSymbolContribution(BaseModel):
    """Per-symbol contribution in one portfolio window."""

    symbol: str
    window_label: str
    status: Literal["passed", "failed", "blocked"]
    blockers: list[str] = Field(default_factory=list)
    trade_count: int = 0
    accepted_trade_count: int = 0
    skipped_exposure_trade_count: int = 0
    net_profit: float = 0.0
    artifact_dir: str | None = None
    summary_json_path: str | None = None


class PortfolioWindowSummary(BaseModel):
    """Combined portfolio scorecard row for one historical window."""

    window_label: str
    start: datetime
    end: datetime
    status: Literal["passed", "failed", "blocked"]
    blockers: list[str] = Field(default_factory=list)
    trade_count: int = 0
    accepted_trade_count: int = 0
    skipped_exposure_trade_count: int = 0
    net_profit: float = 0.0
    max_drawdown: float | None = None
    profit_factor: float | None = None
    net_profit_buffer: float = 0.0
    profit_factor_buffer: float | None = None
    max_drawdown_buffer: float | None = None
    symbol_count: int = 0
    blocked_symbol_count: int = 0
    equity_curve_path: str | None = None
    contribution_csv_path: str | None = None
    trade_csv_path: str | None = None
    regime_csv_path: str | None = None


class PortfolioRegimeContribution(BaseModel):
    """Per-regime PnL/drawdown contribution for one portfolio window."""

    window_label: str
    regime_label: Literal["bull_long", "bear_short_or_avoid", "neutral_blocked"]
    regime_decision: Literal["long_enabled", "risk_off_blocked"]
    trade_count: int = 0
    accepted_trade_count: int = 0
    skipped_blocked_signal_count: int = 0
    pnl_contribution: float = 0.0
    drawdown_contribution: float = 0.0


class PortfolioAggregate(BaseModel):
    """Aggregate portfolio verdict across windows."""

    window_count: int
    passed_window_count: int
    failed_window_count: int
    technical_pass: bool
    hypothesis_supported: bool
    hypothesis_not_supported: bool
    blockers: list[str] = Field(default_factory=list)
    thresholds: ResearchThresholds
    starting_equity: float
    max_trade_notional: float
    max_total_open_notional: float


class PortfolioExperimentSummary(BaseModel):
    """Portfolio batch summary written to JSON."""

    portfolio_id: str
    universe: str
    symbols: list[str]
    starting_equity: float
    max_trade_notional: float
    max_total_open_notional: float
    gate_profile: str
    cost_model_settings: dict[str, float]
    windows: list[PortfolioWindowSummary]
    aggregate: PortfolioAggregate
    per_symbol_contributions: list[PortfolioSymbolContribution]
    per_regime_contributions: list[PortfolioRegimeContribution]
    summary_json_path: str
    summary_csv_path: str
    contribution_csv_path: str
    regime_csv_path: str


@dataclass(frozen=True)
class PortfolioExperimentResult:
    """Paths and parsed summary returned by the portfolio runner."""

    portfolio_id: str
    summary: PortfolioExperimentSummary
    summary_json_path: Path
    summary_csv_path: Path
    contribution_csv_path: Path
    artifact_dir: Path


def run_portfolio_batch_experiment(
    *,
    windows: list[BatchWindow],
    universe: str = "fixed-50-altcoins",
    symbols: tuple[str, ...] | None = None,
    output_dir: str | Path = "artifacts/altcoin-universe-portfolio-comparison",
    market_data_dir: str | Path = "artifacts/batch-market-data",
    gate_profile: str,
    thresholds: ResearchThresholds | None = None,
    starting_equity: float = 10_000.0,
    max_trade_notional: float = 1_000.0,
    max_total_open_notional: float = 3_000.0,
    spread: float = 1.0,
    slippage: float = 0.5,
    commission_rate: float = 0.00055,
    funding_rate_per_bar: float = 0.00001,
    reuse_market_data: bool = False,
    stop_on_symbol_error: bool = False,
    max_workers: int = 4,
    run_symbol_batch: RunSymbolBatchCallable = run_batch_experiment,
) -> PortfolioExperimentResult:
    """Run approved symbols as one shared-bankroll portfolio and write artifacts."""

    if starting_equity <= 0:
        msg = "starting_equity must be positive"
        raise ValueError(msg)
    if max_trade_notional <= 0 or max_total_open_notional <= 0:
        msg = "portfolio notional caps must be positive"
        raise ValueError(msg)
    if max_workers <= 0:
        msg = "max_workers must be positive"
        raise ValueError(msg)
    active_symbols = list(symbols or resolve_crypto_research_universe(universe))
    active_thresholds = thresholds or ResearchThresholds()
    cost_model_settings = {
        "spread": spread,
        "slippage_per_unit": slippage,
        "commission_rate": commission_rate,
        "funding_rate_per_bar": funding_rate_per_bar,
    }
    portfolio_id = _portfolio_id(
        universe=universe,
        symbols=active_symbols,
        windows=windows,
        gate_profile=gate_profile,
        thresholds=active_thresholds,
        starting_equity=starting_equity,
        max_trade_notional=max_trade_notional,
        max_total_open_notional=max_total_open_notional,
        cost_model_settings=cost_model_settings,
    )
    artifact_dir = Path(output_dir) / gate_profile / portfolio_id
    artifact_dir.mkdir(parents=True, exist_ok=True)

    symbol_results: dict[str, BatchExperimentResult] = {}
    symbol_failures: dict[str, str] = {}
    def evaluate_symbol(symbol: str) -> tuple[str, BatchExperimentResult]:
        return symbol, run_symbol_batch(
            windows=windows,
            output_dir=artifact_dir / "runs",
            market_data_dir=market_data_dir,
            thresholds=active_thresholds,
            gate_profile=gate_profile,
            reuse_market_data=reuse_market_data,
            spread=spread,
            slippage=slippage,
            commission_rate=commission_rate,
            funding_rate_per_bar=funding_rate_per_bar,
            symbol=symbol,
            continue_on_error=True,
        )

    if max_workers == 1:
        for symbol in active_symbols:
            try:
                result_symbol, result = evaluate_symbol(symbol)
                symbol_results[result_symbol] = result
            except Exception as exc:  # noqa: BLE001 - portfolio evidence records unavailable symbols.
                symbol_failures[symbol] = f"symbol_exception:{type(exc).__name__}:{exc}"
                if stop_on_symbol_error:
                    break
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(evaluate_symbol, symbol): symbol for symbol in active_symbols}
            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    result_symbol, result = future.result()
                    symbol_results[result_symbol] = result
                except Exception as exc:  # noqa: BLE001 - portfolio evidence records unavailable symbols.
                    symbol_failures[symbol] = f"symbol_exception:{type(exc).__name__}:{exc}"
                    if stop_on_symbol_error:
                        break

    contributions: list[PortfolioSymbolContribution] = []
    regime_contributions: list[PortfolioRegimeContribution] = []
    portfolio_windows: list[PortfolioWindowSummary] = []
    for window in windows:
        window_contributions = _window_contributions(
            window=window,
            active_symbols=active_symbols,
            symbol_results=symbol_results,
            symbol_failures=symbol_failures,
        )
        trades = _window_trades(window_contributions, window=window)
        window_summary, window_regimes = _portfolio_window_summary(
            window=window,
            contributions=window_contributions,
            trades=trades,
            thresholds=active_thresholds,
            starting_equity=starting_equity,
            max_trade_notional=max_trade_notional,
            max_total_open_notional=max_total_open_notional,
            artifact_dir=artifact_dir,
        )
        portfolio_windows.append(window_summary)
        regime_contributions.extend(window_regimes)
        contributions.extend(window_contributions)

    summary_csv_path = artifact_dir / "portfolio-scorecard.csv"
    contribution_csv_path = artifact_dir / "per-symbol-contributions.csv"
    regime_csv_path = artifact_dir / "per-regime-contributions.csv"
    summary_json_path = artifact_dir / "summary.json"
    aggregate = _portfolio_aggregate(
        portfolio_windows,
        thresholds=active_thresholds,
        starting_equity=starting_equity,
        max_trade_notional=max_trade_notional,
        max_total_open_notional=max_total_open_notional,
    )
    summary = PortfolioExperimentSummary(
        portfolio_id=portfolio_id,
        universe=universe,
        symbols=active_symbols,
        starting_equity=starting_equity,
        max_trade_notional=max_trade_notional,
        max_total_open_notional=max_total_open_notional,
        gate_profile=gate_profile,
        cost_model_settings=cost_model_settings,
        windows=portfolio_windows,
        aggregate=aggregate,
        per_symbol_contributions=contributions,
        per_regime_contributions=regime_contributions,
        summary_json_path=str(summary_json_path),
        summary_csv_path=str(summary_csv_path),
        contribution_csv_path=str(contribution_csv_path),
        regime_csv_path=str(regime_csv_path),
    )
    _write_portfolio_scorecard(summary_csv_path, portfolio_windows)
    _write_contributions(contribution_csv_path, contributions)
    _write_regime_contributions(regime_csv_path, regime_contributions)
    _write_json(summary_json_path, summary.model_dump(mode="json"))
    return PortfolioExperimentResult(
        portfolio_id=portfolio_id,
        summary=summary,
        summary_json_path=summary_json_path,
        summary_csv_path=summary_csv_path,
        contribution_csv_path=contribution_csv_path,
        artifact_dir=artifact_dir,
    )


def _window_contributions(
    *,
    window: BatchWindow,
    active_symbols: Iterable[str],
    symbol_results: dict[str, BatchExperimentResult],
    symbol_failures: dict[str, str],
) -> list[PortfolioSymbolContribution]:
    output: list[PortfolioSymbolContribution] = []
    for symbol in active_symbols:
        if symbol in symbol_failures:
            output.append(
                PortfolioSymbolContribution(
                    symbol=symbol,
                    window_label=window.label,
                    status="blocked",
                    blockers=[symbol_failures[symbol]],
                )
            )
            continue
        result = symbol_results.get(symbol)
        if result is None:
            output.append(
                PortfolioSymbolContribution(
                    symbol=symbol,
                    window_label=window.label,
                    status="blocked",
                    blockers=["symbol_not_evaluated"],
                )
            )
            continue
        row = next((item for item in result.summary.windows if item.window_label == window.label), None)
        if row is None:
            output.append(
                PortfolioSymbolContribution(
                    symbol=symbol,
                    window_label=window.label,
                    status="blocked",
                    blockers=["window_not_evaluated"],
                    summary_json_path=str(result.summary_json_path),
                )
            )
            continue
        output.append(_contribution_from_row(symbol=symbol, row=row, summary_path=result.summary_json_path))
    return output


def _contribution_from_row(
    *, symbol: str, row: BatchWindowSummary, summary_path: Path
) -> PortfolioSymbolContribution:
    return PortfolioSymbolContribution(
        symbol=symbol,
        window_label=row.window_label,
        status=row.status,
        blockers=row.blockers,
        trade_count=row.trade_count or 0,
        accepted_trade_count=0,
        net_profit=row.net_profit or 0.0,
        artifact_dir=row.artifact_dir,
        summary_json_path=str(summary_path),
    )


def _window_trades(
    contributions: list[PortfolioSymbolContribution], *, window: BatchWindow
) -> list[PortfolioTrade]:
    trades: list[PortfolioTrade] = []
    for contribution in contributions:
        if _contribution_blocks_portfolio(contribution):
            continue
        trades.extend(_read_trade_rows(contribution, window=window))
    return sorted(trades, key=lambda item: (item.entry_time, item.symbol, item.source_trade_id or ""))


def _read_trade_rows(
    contribution: PortfolioSymbolContribution, *, window: BatchWindow
) -> list[PortfolioTrade]:
    if contribution.artifact_dir is None:
        return []
    artifact_dir = Path(contribution.artifact_dir)
    trade_paths = sorted(artifact_dir.glob("*-trades.csv"))
    if not trade_paths:
        if contribution.trade_count <= 0:
            return []
        # Test fakes and blocked smoke artifacts may expose only summary metrics.
        return [
            PortfolioTrade(
                symbol=contribution.symbol,
                window_label=window.label,
                entry_time=to_utc(window.start),
                exit_time=to_utc(window.end),
                net_pnl=contribution.net_profit,
                notional=0.0,
                source_artifact_dir=str(artifact_dir),
            )
        ]
    feature_rows = _read_entry_feature_rows(artifact_dir)
    output: list[PortfolioTrade] = []
    for trade_path in trade_paths:
        with trade_path.open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                entry_time = to_utc(datetime.fromisoformat(str(row["entry_time"]).replace("Z", "+00:00")))
                exit_time = to_utc(datetime.fromisoformat(str(row["exit_time"]).replace("Z", "+00:00")))
                quantity = _float(row.get("quantity"))
                entry_price = _float(row.get("entry_price"))
                trade_id = str(row.get("trade_id") or "")
                regime_label, regime_decision = _classify_trade_regime(feature_rows.get(trade_id, {}))
                output.append(
                    PortfolioTrade(
                        symbol=contribution.symbol,
                        window_label=window.label,
                        entry_time=entry_time,
                        exit_time=exit_time,
                        net_pnl=_float(row.get("net_pnl")),
                        quantity=quantity,
                        entry_price=entry_price,
                        notional=abs(quantity * entry_price),
                        regime_label=regime_label,
                        regime_decision=regime_decision,
                        source_trade_id=trade_id,
                        source_artifact_dir=str(artifact_dir),
                    )
                )
    return output


def _read_entry_feature_rows(artifact_dir: Path) -> dict[str, dict[str, str]]:
    feature_paths = sorted(artifact_dir.glob("*-entry-feature-snapshots.csv"))
    if not feature_paths:
        return {}
    output: dict[str, dict[str, str]] = {}
    for feature_path in feature_paths:
        with feature_path.open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                trade_id = str(row.get("trade_id") or "")
                if trade_id:
                    output[trade_id] = dict(row)
    return output


def _classify_trade_regime(
    feature_row: dict[str, str],
) -> tuple[
    Literal["bull_long", "bear_short_or_avoid", "neutral_blocked"],
    Literal["long_enabled", "risk_off_blocked"],
]:
    h1 = feature_row.get("feature_context_H1_trend_alignment", "unavailable")
    h4 = feature_row.get("feature_context_H4_trend_alignment", "unavailable")
    d1 = feature_row.get("feature_context_D1_trend_alignment", "unavailable")
    available = {value for value in (h1, h4, d1) if value in {"long", "short_or_flat"}}
    if h1 == "long" and h4 == "long":
        return "bull_long", "long_enabled"
    if available and "long" not in available:
        return "bear_short_or_avoid", "risk_off_blocked"
    return "neutral_blocked", "risk_off_blocked"


def _portfolio_window_summary(
    *,
    window: BatchWindow,
    contributions: list[PortfolioSymbolContribution],
    trades: list[PortfolioTrade],
    thresholds: ResearchThresholds,
    starting_equity: float,
    max_trade_notional: float,
    max_total_open_notional: float,
    artifact_dir: Path,
) -> tuple[PortfolioWindowSummary, list[PortfolioRegimeContribution]]:
    accepted = _apply_exposure_caps(
        trades,
        max_trade_notional=max_trade_notional,
        max_total_open_notional=max_total_open_notional,
    )
    regime_rows = _regime_contributions(window=window, trades=accepted)
    equity_rows, max_drawdown = _portfolio_equity(
        accepted,
        starting_equity=starting_equity,
        window=window,
    )
    net_profit = sum(trade.net_pnl for trade in accepted if trade.accepted)
    gross_profit = sum(trade.net_pnl for trade in accepted if trade.accepted and trade.net_pnl > 0)
    gross_loss = abs(sum(trade.net_pnl for trade in accepted if trade.accepted and trade.net_pnl < 0))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (None if gross_profit <= 0 else 999999.0)
    blocked_symbol_count = sum(1 for item in contributions if _contribution_blocks_portfolio(item))
    skipped_count = sum(1 for trade in accepted if not trade.accepted)
    accepted_count = sum(1 for trade in accepted if trade.accepted)
    blockers = _portfolio_window_blockers(
        trade_count=accepted_count,
        net_profit=net_profit,
        profit_factor=profit_factor,
        max_drawdown=max_drawdown,
        blocked_symbol_count=blocked_symbol_count,
        thresholds=thresholds,
    )
    status: Literal["passed", "failed", "blocked"] = (
        "passed" if not blockers else "blocked" if blocked_symbol_count else "failed"
    )
    window_dir = artifact_dir / window.label
    equity_path = window_dir / "portfolio-equity.csv"
    trade_path = window_dir / "portfolio-trades.csv"
    contribution_path = window_dir / "per-symbol-contributions.csv"
    regime_path = window_dir / "per-regime-contributions.csv"
    _write_csv(equity_path, ["timestamp", "equity", "drawdown"], equity_rows)
    _write_portfolio_trades(trade_path, accepted)
    updated_contributions = _apply_trade_counts_to_contributions(contributions, accepted)
    contributions[:] = updated_contributions
    _write_contributions(contribution_path, contributions)
    _write_regime_contributions(regime_path, regime_rows)
    return PortfolioWindowSummary(
        window_label=window.label,
        start=to_utc(window.start),
        end=to_utc(window.end),
        status=status,
        blockers=blockers,
        trade_count=len(trades),
        accepted_trade_count=accepted_count,
        skipped_exposure_trade_count=skipped_count,
        net_profit=net_profit,
        max_drawdown=max_drawdown,
        profit_factor=profit_factor,
        net_profit_buffer=net_profit - thresholds.min_net_profit,
        profit_factor_buffer=(
            None if profit_factor is None else profit_factor - thresholds.min_profit_factor
        ),
        max_drawdown_buffer=(
            None if max_drawdown is None else max_drawdown - thresholds.min_max_drawdown
        ),
        symbol_count=len(contributions),
        blocked_symbol_count=blocked_symbol_count,
        equity_curve_path=str(equity_path),
        contribution_csv_path=str(contribution_path),
        trade_csv_path=str(trade_path),
        regime_csv_path=str(regime_path),
    ), regime_rows


def _apply_exposure_caps(
    trades: list[PortfolioTrade], *, max_trade_notional: float, max_total_open_notional: float
) -> list[PortfolioTrade]:
    accepted: list[PortfolioTrade] = []
    open_trades: list[PortfolioTrade] = []
    for trade in trades:
        open_trades = [item for item in open_trades if item.exit_time > trade.entry_time]
        current_open = sum(item.notional for item in open_trades if item.accepted)
        if trade.regime_decision != "long_enabled":
            rejected = trade.model_copy(
                update={"accepted": False, "blocker": f"portfolio_regime_{trade.regime_label}"}
            )
            accepted.append(rejected)
            continue
        original_notional = trade.notional or max_trade_notional
        capped_notional = min(original_notional, max_trade_notional)
        if current_open + capped_notional > max_total_open_notional:
            rejected = trade.model_copy(
                update={"accepted": False, "blocker": "portfolio_total_exposure_cap_exceeded"}
            )
            accepted.append(rejected)
            continue
        scale = capped_notional / original_notional if original_notional > 0 else 1.0
        adjusted = trade.model_copy(update={"notional": capped_notional, "net_pnl": trade.net_pnl * scale})
        accepted.append(adjusted)
        open_trades.append(adjusted)
    return accepted


def _regime_contributions(
    *, window: BatchWindow, trades: list[PortfolioTrade]
) -> list[PortfolioRegimeContribution]:
    rows: list[PortfolioRegimeContribution] = []
    regime_plan: tuple[
        tuple[
            Literal["bull_long", "bear_short_or_avoid", "neutral_blocked"],
            Literal["long_enabled", "risk_off_blocked"],
        ],
        ...,
    ] = (
        ("bull_long", "long_enabled"),
        ("bear_short_or_avoid", "risk_off_blocked"),
        ("neutral_blocked", "risk_off_blocked"),
    )
    for regime_label, decision in regime_plan:
        regime_trades = [trade for trade in trades if trade.regime_label == regime_label]
        accepted = [trade for trade in regime_trades if trade.accepted]
        pnl = sum(trade.net_pnl for trade in accepted)
        rows.append(
            PortfolioRegimeContribution(
                window_label=window.label,
                regime_label=regime_label,
                regime_decision=decision,
                trade_count=len(regime_trades),
                accepted_trade_count=len(accepted),
                skipped_blocked_signal_count=sum(1 for trade in regime_trades if not trade.accepted),
                pnl_contribution=pnl,
                drawdown_contribution=min(pnl, 0.0) / 10_000.0,
            )
        )
    return rows


def _portfolio_equity(
    trades: list[PortfolioTrade], *, starting_equity: float, window: BatchWindow
) -> tuple[list[dict[str, object]], float]:
    equity = starting_equity
    peak = starting_equity
    rows: list[dict[str, object]] = [
        {"timestamp": to_utc(window.start).isoformat(), "equity": equity, "drawdown": 0.0}
    ]
    max_drawdown = 0.0
    for trade in sorted((item for item in trades if item.accepted), key=lambda item: item.exit_time):
        equity += trade.net_pnl
        peak = max(peak, equity)
        drawdown = (equity - peak) / peak if peak > 0 else 0.0
        max_drawdown = min(max_drawdown, drawdown)
        rows.append({"timestamp": trade.exit_time.isoformat(), "equity": equity, "drawdown": drawdown})
    rows.append({"timestamp": to_utc(window.end).isoformat(), "equity": equity, "drawdown": max_drawdown})
    return rows, max_drawdown


def _portfolio_window_blockers(
    *,
    trade_count: int,
    net_profit: float,
    profit_factor: float | None,
    max_drawdown: float | None,
    blocked_symbol_count: int,
    thresholds: ResearchThresholds,
) -> list[str]:
    blockers: list[str] = []
    if blocked_symbol_count:
        blockers.append("portfolio_symbol_blockers_present")
    if trade_count < thresholds.min_trade_count:
        blockers.append("trade_count_below_threshold")
    if net_profit <= thresholds.min_net_profit:
        blockers.append("net_profit_below_threshold")
    if profit_factor is None or profit_factor <= thresholds.min_profit_factor:
        blockers.append("profit_factor_below_threshold")
    if max_drawdown is None or max_drawdown < thresholds.min_max_drawdown:
        blockers.append("max_drawdown_below_threshold")
    return blockers


def _contribution_blocks_portfolio(contribution: PortfolioSymbolContribution) -> bool:
    """Return true only for symbol blockers that make portfolio evidence incomplete."""

    technical_prefixes = (
        "symbol_exception:",
        "symbol_not_evaluated",
        "window_not_evaluated",
        "window_exception:",
        "missing_feed_gap_count",
        "feed_gaps_present",
        "context_timeframes_missing",
    )
    return any(
        blocker == prefix or blocker.startswith(prefix)
        for blocker in contribution.blockers
        for prefix in technical_prefixes
    )


def _apply_trade_counts_to_contributions(
    contributions: list[PortfolioSymbolContribution], trades: list[PortfolioTrade]
) -> list[PortfolioSymbolContribution]:
    output: list[PortfolioSymbolContribution] = []
    for contribution in contributions:
        symbol_trades = [trade for trade in trades if trade.symbol == contribution.symbol]
        output.append(
            contribution.model_copy(
                update={
                    "accepted_trade_count": sum(1 for trade in symbol_trades if trade.accepted),
                    "skipped_exposure_trade_count": sum(1 for trade in symbol_trades if not trade.accepted),
                    "net_profit": sum(trade.net_pnl for trade in symbol_trades if trade.accepted),
                }
            )
        )
    return output


def _portfolio_aggregate(
    windows: list[PortfolioWindowSummary],
    *,
    thresholds: ResearchThresholds,
    starting_equity: float,
    max_trade_notional: float,
    max_total_open_notional: float,
) -> PortfolioAggregate:
    failed = [window for window in windows if window.status != "passed"]
    blockers = [f"{window.window_label}:{blocker}" for window in failed for blocker in window.blockers]
    supported = bool(windows) and not failed
    technical_pass = bool(windows) and not any(
        _portfolio_window_has_technical_blocker(window) for window in windows
    )
    return PortfolioAggregate(
        window_count=len(windows),
        passed_window_count=len(windows) - len(failed),
        failed_window_count=len(failed),
        technical_pass=technical_pass,
        hypothesis_supported=supported,
        hypothesis_not_supported=not supported,
        blockers=blockers,
        thresholds=thresholds,
        starting_equity=starting_equity,
        max_trade_notional=max_trade_notional,
        max_total_open_notional=max_total_open_notional,
    )


def _portfolio_window_has_technical_blocker(window: PortfolioWindowSummary) -> bool:
    technical_blockers = {"portfolio_symbol_blockers_present"}
    return any(blocker in technical_blockers for blocker in window.blockers)


def _portfolio_id(**payload: Any) -> str:
    text = json.dumps(_jsonable(payload), sort_keys=True, ensure_ascii=False)
    import hashlib

    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, datetime):
        return to_utc(value).isoformat()
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def _float(value: object) -> float:
    if value is None or value == "":
        return 0.0
    return float(cast(float | int | str, value))


def _write_portfolio_scorecard(path: Path, windows: list[PortfolioWindowSummary]) -> None:
    _write_csv(
        path,
        [
            "window_label",
            "status",
            "blockers",
            "trade_count",
            "accepted_trade_count",
            "skipped_exposure_trade_count",
            "net_profit",
            "net_profit_buffer",
            "profit_factor",
            "profit_factor_buffer",
            "max_drawdown",
            "max_drawdown_buffer",
            "symbol_count",
            "blocked_symbol_count",
            "equity_curve_path",
            "contribution_csv_path",
            "trade_csv_path",
            "regime_csv_path",
        ],
        [
            {
                **window.model_dump(mode="json"),
                "blockers": ";".join(window.blockers),
            }
            for window in windows
        ],
    )


def _write_contributions(path: Path, contributions: list[PortfolioSymbolContribution]) -> None:
    _write_csv(
        path,
        [
            "window_label",
            "symbol",
            "status",
            "blockers",
            "trade_count",
            "accepted_trade_count",
            "skipped_exposure_trade_count",
            "net_profit",
            "artifact_dir",
            "summary_json_path",
        ],
        [
            {
                **item.model_dump(mode="json"),
                "blockers": ";".join(item.blockers),
            }
            for item in contributions
        ],
    )


def _write_portfolio_trades(path: Path, trades: list[PortfolioTrade]) -> None:
    _write_csv(
        path,
        [
            "window_label",
            "symbol",
            "entry_time",
            "exit_time",
            "net_pnl",
            "quantity",
            "entry_price",
            "notional",
            "accepted",
            "blocker",
            "regime_label",
            "regime_decision",
            "source_trade_id",
            "source_artifact_dir",
        ],
        [trade.model_dump(mode="json") for trade in trades],
    )


def _write_regime_contributions(path: Path, rows: list[PortfolioRegimeContribution]) -> None:
    _write_csv(
        path,
        [
            "window_label",
            "regime_label",
            "regime_decision",
            "trade_count",
            "accepted_trade_count",
            "skipped_blocked_signal_count",
            "pnl_contribution",
            "drawdown_contribution",
        ],
        [row.model_dump(mode="json") for row in rows],
    )


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    try:
        with temp_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    try:
        temp_path.write_text(
            json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _resolve_windows(args: argparse.Namespace) -> list[BatchWindow]:
    selected = [bool(args.preset), bool(args.windows), bool(args.windows_file)]
    if sum(selected) != 1:
        msg = "provide exactly one of --preset, --windows, or --windows-file"
        raise ValueError(msg)
    if args.preset:
        return preset_windows(args.preset)
    if args.windows:
        return parse_windows(args.windows)
    payload = json.loads(Path(args.windows_file).read_text(encoding="utf-8"))
    return [
        BatchWindow(
            label=str(item["label"]),
            start=to_utc(datetime.fromisoformat(str(item["start"]).replace("Z", "+00:00"))),
            end=to_utc(datetime.fromisoformat(str(item["end"]).replace("Z", "+00:00"))),
        )
        for item in payload
    ]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run shared-bankroll public crypto portfolio batches")
    parser.add_argument("--preset", choices=["quarterly-2023-2024"])
    parser.add_argument("--windows")
    parser.add_argument("--windows-file")
    parser.add_argument("--universe", choices=["fixed-50-altcoins", "ethusdt-only"], default="fixed-50-altcoins")
    parser.add_argument("--output-dir", default="artifacts/altcoin-universe-portfolio-comparison")
    parser.add_argument("--market-data-dir", default="artifacts/batch-market-data")
    parser.add_argument("--gate-profile", required=True)
    parser.add_argument("--starting-equity", type=float, default=10_000.0)
    parser.add_argument("--max-trade-notional", type=float, default=1_000.0)
    parser.add_argument("--max-total-open-notional", type=float, default=3_000.0)
    parser.add_argument("--spread", type=float, default=1.0)
    parser.add_argument("--slippage", type=float, default=0.5)
    parser.add_argument("--commission-rate", type=float, default=0.00055)
    parser.add_argument("--funding-rate-per-bar", type=float, default=0.00001)
    parser.add_argument("--reuse-market-data", action="store_true")
    parser.add_argument("--stop-on-symbol-error", action="store_true")
    parser.add_argument("--max-workers", type=int, default=4)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = run_portfolio_batch_experiment(
        windows=_resolve_windows(args),
        universe=args.universe,
        output_dir=args.output_dir,
        market_data_dir=args.market_data_dir,
        gate_profile=args.gate_profile,
        starting_equity=args.starting_equity,
        max_trade_notional=args.max_trade_notional,
        max_total_open_notional=args.max_total_open_notional,
        spread=args.spread,
        slippage=args.slippage,
        commission_rate=args.commission_rate,
        funding_rate_per_bar=args.funding_rate_per_bar,
        reuse_market_data=args.reuse_market_data,
        stop_on_symbol_error=args.stop_on_symbol_error,
        max_workers=args.max_workers,
    )
    print(json.dumps(result.summary.model_dump(mode="json"), sort_keys=True, indent=2, ensure_ascii=False))
    return 0


__all__ = [
    "PortfolioExperimentResult",
    "PortfolioExperimentSummary",
    "PortfolioWindowSummary",
    "fixed_altcoin_research_universe",
    "run_portfolio_batch_experiment",
]


if __name__ == "__main__":
    raise SystemExit(main())
