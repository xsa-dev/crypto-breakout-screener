"""Deterministic realistic-cost robustness comparison for BTCUSDT batch profiles."""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal

from pydantic import BaseModel, Field

from src.app.breakout.experiments.crypto_batch import ResearchThresholds

REALISTIC_COST_SETTINGS: dict[str, float] = {
    "spread": 1.0,
    "slippage_per_unit": 0.5,
    "commission_per_unit": 0.0,
    "funding_per_bar": 0.0,
    "commission_rate": 0.00055,
    "funding_rate_per_bar": 0.00001,
}
REQUIRED_QUARTERS: tuple[str, ...] = (
    "2023q1",
    "2023q2",
    "2023q3",
    "2023q4",
    "2024q1",
    "2024q2",
    "2024q3",
    "2024q4",
)
SCORECARD_COLUMNS = [
    "candidate",
    "cost_scenario",
    "window_label",
    "status",
    "blockers",
    "trade_count",
    "net_profit",
    "profit_factor",
    "max_drawdown",
    "feed_gap_count",
    "source_artifact_dir",
]
Classification = Literal[
    "net_costs_supported",
    "baseline_only_insufficient",
    "falsified_realistic_costs",
    "technical_blocked",
    "not_supported",
]


class RevaluedWindow(BaseModel):
    """One quarterly window revalued under a named cost scenario."""

    candidate: str
    cost_scenario: Literal["baseline", "realistic"]
    window_label: str
    status: Literal["passed", "blocked", "unknown"]
    blockers: list[str] = Field(default_factory=list)
    trade_count: int = 0
    net_profit: float | None = None
    profit_factor: float | None = None
    max_drawdown: float | None = None
    feed_gap_count: int | None = None
    source_artifact_dir: str | None = None


class CandidateRobustnessSummary(BaseModel):
    """Robustness verdict for one fixed candidate profile."""

    candidate: str
    classification: Classification
    required_windows: list[str]
    thresholds: dict[str, Any]
    baseline_cost_model_settings: dict[str, Any]
    realistic_cost_model_settings: dict[str, float]
    baseline_passed_count: int
    realistic_passed_count: int
    baseline_windows: list[RevaluedWindow]
    realistic_windows: list[RevaluedWindow]
    blockers: list[str] = Field(default_factory=list)
    source_summary_path: str
    summary_json_path: str
    scorecard_csv_path: str


@dataclass(frozen=True)
class SearchResult:
    """Paths and parsed summaries produced by a robustness comparison run."""

    summaries: list[CandidateRobustnessSummary]
    summary_json_path: Path
    scorecard_csv_path: Path


def run_realistic_cost_profile_search(
    *,
    candidate_summary_paths: Iterable[str | Path],
    output_dir: str | Path = "artifacts/realistic-cost-profile-search",
    thresholds: ResearchThresholds | None = None,
    realistic_cost_settings: dict[str, float] | None = None,
) -> SearchResult:
    """Revalue fixed candidate batch trade ledgers under conservative realistic costs."""

    active_thresholds = thresholds or ResearchThresholds()
    cost_settings = dict(realistic_cost_settings or REALISTIC_COST_SETTINGS)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summaries: list[CandidateRobustnessSummary] = []
    for source_path in candidate_summary_paths:
        source_summary_path = Path(source_path)
        payload = _read_json(source_summary_path)
        candidate = _candidate_name(payload)
        baseline_windows = _baseline_windows(payload, candidate=candidate, thresholds=active_thresholds)
        realistic_windows = _realistic_windows(
            payload,
            candidate=candidate,
            source_summary_path=source_summary_path,
            thresholds=active_thresholds,
            cost_settings=cost_settings,
        )
        baseline_passed = sum(row.status == "passed" for row in baseline_windows)
        realistic_passed = sum(row.status == "passed" for row in realistic_windows)
        blockers = [
            f"{row.window_label}:{blocker}"
            for row in realistic_windows
            if row.status != "passed"
            for blocker in row.blockers
        ]
        classification = _classification(
            baseline_passed=baseline_passed,
            realistic_passed=realistic_passed,
            realistic_windows=realistic_windows,
        )
        candidate_dir = out_dir / _safe_name(candidate)
        candidate_dir.mkdir(parents=True, exist_ok=True)
        summary_json_path = candidate_dir / "summary.json"
        scorecard_csv_path = candidate_dir / "scorecard.csv"
        summary = CandidateRobustnessSummary(
            candidate=candidate,
            classification=classification,
            required_windows=list(REQUIRED_QUARTERS),
            thresholds=active_thresholds.model_dump(mode="json"),
            baseline_cost_model_settings=dict(payload.get("cost_model_settings") or {}),
            realistic_cost_model_settings=cost_settings,
            baseline_passed_count=baseline_passed,
            realistic_passed_count=realistic_passed,
            baseline_windows=baseline_windows,
            realistic_windows=realistic_windows,
            blockers=blockers,
            source_summary_path=str(source_summary_path),
            summary_json_path=str(summary_json_path),
            scorecard_csv_path=str(scorecard_csv_path),
        )
        _write_candidate_summary(summary_json_path, summary)
        _write_candidate_scorecard(scorecard_csv_path, summary)
        summaries.append(summary)

    combined_summary_path = out_dir / "summary.json"
    combined_scorecard_path = out_dir / "scorecard.csv"
    _write_combined_summary(combined_summary_path, summaries, cost_settings=cost_settings)
    _write_combined_scorecard(combined_scorecard_path, summaries)
    return SearchResult(
        summaries=summaries,
        summary_json_path=combined_summary_path,
        scorecard_csv_path=combined_scorecard_path,
    )


def _candidate_name(payload: dict[str, Any]) -> str:
    exit_profile = str(payload.get("exit_profile") or "none")
    if exit_profile != "none":
        return exit_profile
    return str(payload.get("gate_profile") or "unknown-profile")


def _baseline_windows(
    payload: dict[str, Any],
    *,
    candidate: str,
    thresholds: ResearchThresholds,
) -> list[RevaluedWindow]:
    rows = []
    windows = _required_windows(payload)
    for window in windows:
        row = RevaluedWindow(
            candidate=candidate,
            cost_scenario="baseline",
            window_label=str(window.get("window_label")),
            status="passed" if window.get("status") == "passed" else "blocked",
            blockers=[str(item) for item in window.get("blockers", [])],
            trade_count=int(window.get("trade_count") or 0),
            net_profit=_optional_float(window.get("net_profit")),
            profit_factor=_optional_float(window.get("profit_factor")),
            max_drawdown=_optional_float(window.get("max_drawdown")),
            feed_gap_count=_optional_int(window.get("feed_gap_count")),
            source_artifact_dir=_optional_str(window.get("artifact_dir")),
        )
        blockers = _threshold_blockers(row, thresholds=thresholds)
        if blockers:
            row = row.model_copy(update={"status": "blocked", "blockers": blockers})
        rows.append(row)
    return rows


def _realistic_windows(
    payload: dict[str, Any],
    *,
    candidate: str,
    source_summary_path: Path,
    thresholds: ResearchThresholds,
    cost_settings: dict[str, float],
) -> list[RevaluedWindow]:
    rows = []
    for window in _required_windows(payload):
        row = _revalue_window(
            window,
            candidate=candidate,
            source_summary_path=source_summary_path,
            cost_settings=cost_settings,
        )
        blockers = _threshold_blockers(row, thresholds=thresholds) if row.status != "unknown" else []
        if blockers:
            row = row.model_copy(update={"status": "blocked", "blockers": blockers})
        rows.append(row)
    return rows


def _required_windows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    windows = payload.get("windows")
    if not isinstance(windows, list):
        msg = "candidate summary must contain windows"
        raise ValueError(msg)
    by_label = {str(window.get("window_label")): window for window in windows if isinstance(window, dict)}
    missing = [label for label in REQUIRED_QUARTERS if label not in by_label]
    if missing:
        msg = f"candidate summary missing required windows: {', '.join(missing)}"
        raise ValueError(msg)
    return [by_label[label] for label in REQUIRED_QUARTERS]


def _revalue_window(
    window: dict[str, Any],
    *,
    candidate: str,
    source_summary_path: Path,
    cost_settings: dict[str, float],
) -> RevaluedWindow:
    artifact_dir = _resolve_artifact_dir(source_summary_path, _optional_str(window.get("artifact_dir")))
    run_id = _optional_str(window.get("run_id"))
    if artifact_dir is None or run_id is None:
        return RevaluedWindow(
            candidate=candidate,
            cost_scenario="realistic",
            window_label=str(window.get("window_label")),
            status="unknown",
            blockers=["missing_source_trade_ledger"],
            source_artifact_dir=_optional_str(window.get("artifact_dir")),
        )
    trades_path = artifact_dir / f"{run_id}-trades.csv"
    if not trades_path.exists():
        return RevaluedWindow(
            candidate=candidate,
            cost_scenario="realistic",
            window_label=str(window.get("window_label")),
            status="unknown",
            blockers=["missing_source_trade_ledger"],
            source_artifact_dir=str(artifact_dir),
        )

    trade_count = 0
    net_profit = 0.0
    gross_profit = 0.0
    gross_loss = 0.0
    equity = 10_000.0
    peak = equity
    max_drawdown = 0.0
    with trades_path.open(newline="", encoding="utf-8") as file:
        for trade in csv.DictReader(file):
            trade_count += 1
            pnl = _revalued_trade_pnl(trade, cost_settings=cost_settings)
            net_profit += pnl
            if pnl > 0:
                gross_profit += pnl
            else:
                gross_loss += pnl
            equity += pnl
            peak = max(peak, equity)
            if peak > 0:
                max_drawdown = min(max_drawdown, (equity - peak) / peak)
    profit_factor = math.inf if gross_loss == 0 and gross_profit > 0 else None
    if gross_loss < 0:
        profit_factor = gross_profit / abs(gross_loss)
    return RevaluedWindow(
        candidate=candidate,
        cost_scenario="realistic",
        window_label=str(window.get("window_label")),
        status="passed",
        trade_count=trade_count,
        net_profit=net_profit,
        profit_factor=profit_factor,
        max_drawdown=max_drawdown,
        feed_gap_count=_optional_int(window.get("feed_gap_count")),
        source_artifact_dir=str(artifact_dir),
    )


def _revalued_trade_pnl(trade: dict[str, str], *, cost_settings: dict[str, float]) -> float:
    entry_price = float(trade["entry_price"])
    exit_price = float(trade["exit_price"])
    quantity = float(trade["quantity"])
    holding_bars = int(float(trade["holding_bars"]))
    gross_pnl = float(trade["gross_pnl"])
    spread_cost = cost_settings["spread"] * quantity
    slippage_cost = cost_settings["slippage_per_unit"] * quantity * 2
    per_unit_commission = cost_settings["commission_per_unit"] * quantity * 2
    per_bar_funding = cost_settings["funding_per_bar"] * quantity * holding_bars
    notional_commission = (entry_price + exit_price) * quantity * cost_settings["commission_rate"]
    notional_funding = entry_price * quantity * cost_settings["funding_rate_per_bar"] * holding_bars
    return gross_pnl - (
        spread_cost
        + slippage_cost
        + per_unit_commission
        + per_bar_funding
        + notional_commission
        + notional_funding
    )


def _threshold_blockers(row: RevaluedWindow, *, thresholds: ResearchThresholds) -> list[str]:
    blockers: list[str] = []
    if row.feed_gap_count is None:
        blockers.append("missing_feed_gap_count")
    elif thresholds.require_no_feed_gaps and row.feed_gap_count != 0:
        blockers.append("feed_gaps_present")
    if row.trade_count < thresholds.min_trade_count:
        blockers.append("trade_count_below_threshold")
    if row.net_profit is None or row.net_profit <= thresholds.min_net_profit:
        blockers.append("net_profit_below_threshold")
    if row.profit_factor is None or row.profit_factor <= thresholds.min_profit_factor:
        blockers.append("profit_factor_below_threshold")
    if row.max_drawdown is None or row.max_drawdown < thresholds.min_max_drawdown:
        blockers.append("max_drawdown_below_threshold")
    return blockers


def _classification(
    *,
    baseline_passed: int,
    realistic_passed: int,
    realistic_windows: list[RevaluedWindow],
) -> Classification:
    if any(row.status == "unknown" for row in realistic_windows):
        return "technical_blocked"
    if realistic_passed == len(REQUIRED_QUARTERS):
        return "net_costs_supported"
    if baseline_passed == len(REQUIRED_QUARTERS):
        return "falsified_realistic_costs"
    if baseline_passed > realistic_passed:
        return "baseline_only_insufficient"
    return "not_supported"


def _resolve_artifact_dir(source_summary_path: Path, artifact_dir: str | None) -> Path | None:
    if artifact_dir is None:
        return None
    path = Path(artifact_dir)
    if path.is_absolute():
        return path
    for parent in (Path.cwd(), source_summary_path.parents[4] if len(source_summary_path.parents) > 4 else None):
        if parent is None:
            continue
        candidate = parent / path
        if candidate.exists():
            return candidate
    return path


def _write_candidate_summary(path: Path, summary: CandidateRobustnessSummary) -> None:
    path.write_text(
        json.dumps(summary.model_dump(mode="json"), sort_keys=True, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _write_combined_summary(
    path: Path,
    summaries: list[CandidateRobustnessSummary],
    *,
    cost_settings: dict[str, float],
) -> None:
    payload = {
        "required_windows": list(REQUIRED_QUARTERS),
        "realistic_cost_model_settings": cost_settings,
        "candidate_count": len(summaries),
        "net_costs_supported_candidates": [
            summary.candidate
            for summary in summaries
            if summary.classification == "net_costs_supported"
        ],
        "best_realistic_passed_count": max(
            (summary.realistic_passed_count for summary in summaries),
            default=0,
        ),
        "candidates": [summary.model_dump(mode="json") for summary in summaries],
    }
    path.write_text(json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_candidate_scorecard(path: Path, summary: CandidateRobustnessSummary) -> None:
    _write_rows(path, [*summary.baseline_windows, *summary.realistic_windows])


def _write_combined_scorecard(path: Path, summaries: list[CandidateRobustnessSummary]) -> None:
    rows: list[RevaluedWindow] = []
    for summary in summaries:
        rows.extend(summary.baseline_windows)
        rows.extend(summary.realistic_windows)
    _write_rows(path, rows)


def _write_rows(path: Path, rows: list[RevaluedWindow]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=SCORECARD_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "candidate": row.candidate,
                    "cost_scenario": row.cost_scenario,
                    "window_label": row.window_label,
                    "status": row.status,
                    "blockers": ";".join(row.blockers),
                    "trade_count": row.trade_count,
                    "net_profit": "" if row.net_profit is None else row.net_profit,
                    "profit_factor": "" if row.profit_factor is None else row.profit_factor,
                    "max_drawdown": "" if row.max_drawdown is None else row.max_drawdown,
                    "feed_gap_count": "" if row.feed_gap_count is None else row.feed_gap_count,
                    "source_artifact_dir": row.source_artifact_dir or "",
                }
            )


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _optional_float(value: object) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str) and value.strip():
        return float(value)
    return None


def _optional_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip():
        return int(float(value))
    return None


def _optional_str(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Revalue BTCUSDT batch profiles under realistic costs")
    parser.add_argument("summary", nargs="+", help="Candidate batch summary.json paths")
    parser.add_argument("--output-dir", default="artifacts/realistic-cost-profile-search")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = run_realistic_cost_profile_search(
        candidate_summary_paths=args.summary,
        output_dir=args.output_dir,
    )
    payload = json.loads(result.summary_json_path.read_text(encoding="utf-8"))
    print(json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
