"""BTCUSDT public-data batch research runner.

This module orchestrates repeated public-data BTCUSDT experiment runs over
explicit historical windows. It is deliberately local, unauthenticated, and
research-only: it does not read .env, exchange credentials, private account
state, or live trading endpoints.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, Field

from src.app.breakout.backtesting import stable_hash
from src.app.breakout.experiments.crypto_backtest import (
    CryptoExperimentResult,
    PublicDownloadResult,
    download_bybit_public_ohlcv_sync,
    run_crypto_experiment,
)
from src.app.breakout.normalizer import to_utc
from src.core.enums import TimeFrame

BATCH_SUMMARY_COLUMNS = [
    "window_label",
    "start",
    "end",
    "status",
    "blockers",
    "run_id",
    "dataset_hash",
    "config_hash",
    "bar_count",
    "trade_count",
    "net_profit",
    "max_drawdown",
    "profit_factor",
    "win_rate",
    "sharpe_ratio",
    "average_trade",
    "expectancy",
    "feed_gap_count",
    "context_timeframes_available",
    "downloaded_csv_paths_json",
    "manifest_path",
    "artifact_dir",
]
RESEARCH_ONLY_NOTICE = "research-only; not production OOS/full-auto approval"
TECHNICAL_BLOCKERS = {
    "missing_feed_gap_count",
    "feed_gaps_present",
    "missing_trade_count",
    "missing_net_profit",
    "missing_profit_factor",
    "missing_max_drawdown",
    "context_timeframes_missing",
}


class BatchWindow(BaseModel):
    """Explicit historical window evaluated by the BTCUSDT batch runner."""

    label: str
    start: datetime
    end: datetime


class ResearchThresholds(BaseModel):
    """Research-screen thresholds, distinct from production OOS approval gates."""

    min_trade_count: int = 1
    min_net_profit: float = 0.0
    min_profit_factor: float = 1.0
    min_max_drawdown: float = -0.35
    require_no_feed_gaps: bool = True


class BatchWindowSummary(BaseModel):
    """One row in the batch research summary."""

    window_label: str
    start: datetime
    end: datetime
    status: Literal["passed", "failed", "blocked"]
    blockers: list[str] = Field(default_factory=list)
    run_id: str | None = None
    dataset_hash: str | None = None
    config_hash: str | None = None
    bar_count: int | None = None
    trade_count: int | None = None
    net_profit: float | None = None
    max_drawdown: float | None = None
    profit_factor: float | None = None
    win_rate: float | None = None
    sharpe_ratio: float | None = None
    average_trade: float | None = None
    expectancy: float | None = None
    feed_gap_count: int | None = None
    context_timeframes_available: list[str] = Field(default_factory=list)
    downloaded_csv_paths: dict[str, str] = Field(default_factory=dict)
    manifest_path: str | None = None
    artifact_dir: str | None = None


class BatchAggregate(BaseModel):
    """Aggregate batch metrics and conservative research verdict."""

    window_count: int
    passed_window_count: int
    failed_window_count: int
    technical_pass: bool
    hypothesis_supported: bool
    hypothesis_not_supported: bool
    research_notice: str = RESEARCH_ONLY_NOTICE
    blockers: list[str] = Field(default_factory=list)
    total_trade_count: int
    total_net_profit: float
    worst_max_drawdown: float | None
    mean_profit_factor: float | None
    mean_win_rate: float | None
    mean_sharpe_ratio: float | None
    thresholds: ResearchThresholds


class BatchExperimentSummary(BaseModel):
    """Complete batch summary written as JSON and CSV."""

    batch_id: str
    symbol: Literal["BTCUSDT"] = "BTCUSDT"
    market: Literal["crypto"] = "crypto"
    source: Literal["bybit_public"] = "bybit_public"
    execution_timeframe: Literal["M15"] = "M15"
    context_timeframes: list[str] = Field(default_factory=lambda: ["H1", "H4", "D1"])
    windows: list[BatchWindowSummary]
    aggregate: BatchAggregate
    summary_csv_path: str
    summary_json_path: str


@dataclass(frozen=True)
class BatchExperimentResult:
    """Paths and parsed summary returned by the batch runner."""

    batch_id: str
    summary: BatchExperimentSummary
    summary_csv_path: Path
    summary_json_path: Path
    artifact_dir: Path


DownloadCallable = Callable[..., PublicDownloadResult]
RunCallable = Callable[..., CryptoExperimentResult]


def _parse_required_datetime(value: str) -> datetime:
    return to_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))


def _dt(value: str) -> datetime:
    return _parse_required_datetime(value)


QUARTERLY_2023_2024_WINDOWS = (
    BatchWindow(label="2023q1", start=_dt("2023-01-01T00:00:00Z"), end=_dt("2023-04-01T00:00:00Z")),
    BatchWindow(label="2023q2", start=_dt("2023-04-01T00:00:00Z"), end=_dt("2023-07-01T00:00:00Z")),
    BatchWindow(label="2023q3", start=_dt("2023-07-01T00:00:00Z"), end=_dt("2023-10-01T00:00:00Z")),
    BatchWindow(label="2023q4", start=_dt("2023-10-01T00:00:00Z"), end=_dt("2024-01-01T00:00:00Z")),
    BatchWindow(label="2024q1", start=_dt("2024-01-01T00:00:00Z"), end=_dt("2024-04-01T00:00:00Z")),
    BatchWindow(label="2024q2", start=_dt("2024-04-01T00:00:00Z"), end=_dt("2024-07-01T00:00:00Z")),
    BatchWindow(label="2024q3", start=_dt("2024-07-01T00:00:00Z"), end=_dt("2024-10-01T00:00:00Z")),
    BatchWindow(label="2024q4", start=_dt("2024-10-01T00:00:00Z"), end=_dt("2025-01-01T00:00:00Z")),
)


def run_batch_experiment(
    *,
    windows: list[BatchWindow],
    output_dir: str | Path = "artifacts/batch-backtests",
    market_data_dir: str | Path = "artifacts/batch-market-data",
    thresholds: ResearchThresholds | None = None,
    symbol: str = "BTCUSDT",
    continue_on_error: bool = True,
    download: DownloadCallable = download_bybit_public_ohlcv_sync,
    run_single: RunCallable = run_crypto_experiment,
) -> BatchExperimentResult:
    """Run BTCUSDT public-data research experiments over multiple windows."""

    _validate_batch_inputs(symbol=symbol, windows=windows)
    active_thresholds = thresholds or ResearchThresholds()
    batch_id = _batch_id(windows=windows, thresholds=active_thresholds)
    artifact_dir = Path(output_dir) / "crypto" / symbol / batch_id
    artifact_dir.mkdir(parents=True, exist_ok=True)

    rows: list[BatchWindowSummary] = []
    for window in windows:
        try:
            row = _run_batch_window(
                window=window,
                output_dir=output_dir,
                market_data_dir=market_data_dir,
                symbol=symbol,
                thresholds=active_thresholds,
                download=download,
                run_single=run_single,
            )
        except Exception as exc:  # noqa: BLE001 - batch summaries must record failed windows.
            row = BatchWindowSummary(
                window_label=window.label,
                start=to_utc(window.start),
                end=to_utc(window.end),
                status="failed",
                blockers=[f"window_exception:{type(exc).__name__}:{exc}"],
            )
            if not continue_on_error:
                rows.append(row)
                break
        rows.append(row)

    aggregate = _aggregate_rows(rows, thresholds=active_thresholds)
    summary_csv_path = artifact_dir / "summary.csv"
    summary_json_path = artifact_dir / "summary.json"
    summary = BatchExperimentSummary(
        batch_id=batch_id,
        windows=rows,
        aggregate=aggregate,
        summary_csv_path=str(summary_csv_path),
        summary_json_path=str(summary_json_path),
    )
    _write_summary_csv(summary_csv_path, rows)
    _write_summary_json(summary_json_path, summary)
    return BatchExperimentResult(
        batch_id=batch_id,
        summary=summary,
        summary_csv_path=summary_csv_path,
        summary_json_path=summary_json_path,
        artifact_dir=artifact_dir,
    )


def load_windows_file(path: str | Path) -> list[BatchWindow]:
    """Load batch windows from a JSON file containing a list of objects."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        msg = "windows file must contain a JSON list"
        raise ValueError(msg)
    return [
        BatchWindow(
            label=str(item["label"]),
            start=_parse_required_datetime(str(item["start"])),
            end=_parse_required_datetime(str(item["end"])),
        )
        for item in payload
    ]


def parse_windows(value: str) -> list[BatchWindow]:
    """Parse CLI windows: label:start:end,label:start:end."""

    windows: list[BatchWindow] = []
    for raw_item in value.split(","):
        item = raw_item.strip()
        if not item:
            continue
        parts = item.split(":", maxsplit=1)
        if len(parts) != 2:
            msg = "each window must be label:start/end"
            raise ValueError(msg)
        label, range_text = parts
        range_parts = range_text.split("/", maxsplit=1)
        if len(range_parts) != 2:
            msg = "each window range must be start/end"
            raise ValueError(msg)
        windows.append(
            BatchWindow(
                label=label,
                start=_parse_required_datetime(range_parts[0]),
                end=_parse_required_datetime(range_parts[1]),
            )
        )
    return windows


def preset_windows(name: str) -> list[BatchWindow]:
    """Return a named batch window preset."""

    if name == "quarterly-2023-2024":
        return list(QUARTERLY_2023_2024_WINDOWS)
    msg = f"unsupported batch preset: {name}"
    raise ValueError(msg)


def _run_batch_window(
    *,
    window: BatchWindow,
    output_dir: str | Path,
    market_data_dir: str | Path,
    symbol: str,
    thresholds: ResearchThresholds,
    download: DownloadCallable,
    run_single: RunCallable,
) -> BatchWindowSummary:
    start = to_utc(window.start)
    end = to_utc(window.end)
    downloaded = download(
        start=start,
        end=end,
        output_dir=market_data_dir,
        symbol=symbol,
    )
    context_paths = {
        timeframe: path
        for timeframe, path in downloaded.csv_paths.items()
        if timeframe != TimeFrame.M15.value
    }
    result = run_single(
        csv_path=downloaded.csv_paths[TimeFrame.M15.value],
        output_dir=output_dir,
        symbol=symbol,
        source="bybit_public",
        context_csv_paths=context_paths,
        source_metadata=downloaded.source_metadata,
    )
    metrics = _read_metrics(result.artifact_dir / f"{result.run_id}-metrics.csv")
    manifest = _read_manifest(result.manifest_path)
    feed_gap_count = len(cast(list[Any], manifest.get("feed_gaps", [])))
    available_context = [str(item) for item in manifest.get("available_context_timeframes", [])]
    row = BatchWindowSummary(
        window_label=window.label,
        start=start,
        end=end,
        status="passed",
        run_id=result.run_id,
        dataset_hash=result.dataset_hash,
        config_hash=result.config_hash,
        bar_count=result.bar_count,
        trade_count=int(metrics.get("trade_count", result.trade_count)),
        net_profit=float(metrics.get("net_profit", result.net_pnl)),
        max_drawdown=float(metrics.get("max_drawdown", result.max_drawdown)),
        profit_factor=_optional_float(metrics.get("profit_factor")),
        win_rate=float(metrics.get("win_rate", result.win_rate)),
        sharpe_ratio=_optional_float(metrics.get("sharpe_ratio")),
        average_trade=_optional_float(metrics.get("average_trade")),
        expectancy=_optional_float(metrics.get("expectancy")),
        feed_gap_count=feed_gap_count,
        context_timeframes_available=available_context,
        downloaded_csv_paths=downloaded.csv_paths,
        manifest_path=str(result.manifest_path),
        artifact_dir=str(result.artifact_dir),
    )
    blockers = _window_blockers(row, thresholds=thresholds)
    if blockers:
        return row.model_copy(update={"status": "blocked", "blockers": blockers})
    return row


def _window_blockers(row: BatchWindowSummary, *, thresholds: ResearchThresholds) -> list[str]:
    blockers: list[str] = []
    if row.feed_gap_count is None:
        blockers.append("missing_feed_gap_count")
    elif thresholds.require_no_feed_gaps and row.feed_gap_count != 0:
        blockers.append("feed_gaps_present")
    if row.trade_count is None:
        blockers.append("missing_trade_count")
    elif row.trade_count < thresholds.min_trade_count:
        blockers.append("trade_count_below_threshold")
    if row.net_profit is None:
        blockers.append("missing_net_profit")
    elif row.net_profit <= thresholds.min_net_profit:
        blockers.append("net_profit_below_threshold")
    if row.profit_factor is None:
        blockers.append("missing_profit_factor")
    elif row.profit_factor <= thresholds.min_profit_factor:
        blockers.append("profit_factor_below_threshold")
    if row.max_drawdown is None:
        blockers.append("missing_max_drawdown")
    elif row.max_drawdown < thresholds.min_max_drawdown:
        blockers.append("max_drawdown_below_threshold")
    if set(row.context_timeframes_available) != {TimeFrame.H1.value, TimeFrame.H4.value, TimeFrame.D1.value}:
        blockers.append("context_timeframes_missing")
    return blockers


def _aggregate_rows(rows: list[BatchWindowSummary], *, thresholds: ResearchThresholds) -> BatchAggregate:
    aggregate_blockers: list[str] = []
    passed_rows = [row for row in rows if row.status == "passed"]
    failed_rows = [row for row in rows if row.status != "passed"]
    for row in failed_rows:
        aggregate_blockers.extend(f"{row.window_label}:{blocker}" for blocker in row.blockers)
    technical_pass = bool(rows) and all(_row_is_technical_pass(row) for row in rows)
    hypothesis_supported = technical_pass and not failed_rows
    hypothesis_not_supported = not hypothesis_supported
    return BatchAggregate(
        window_count=len(rows),
        passed_window_count=len(passed_rows),
        failed_window_count=len(failed_rows),
        technical_pass=technical_pass,
        hypothesis_supported=hypothesis_supported,
        hypothesis_not_supported=hypothesis_not_supported,
        blockers=aggregate_blockers,
        total_trade_count=sum(row.trade_count or 0 for row in rows),
        total_net_profit=sum(row.net_profit or 0.0 for row in rows),
        worst_max_drawdown=_min_optional(row.max_drawdown for row in rows),
        mean_profit_factor=_mean_optional(row.profit_factor for row in passed_rows),
        mean_win_rate=_mean_optional(row.win_rate for row in passed_rows),
        mean_sharpe_ratio=_mean_optional(row.sharpe_ratio for row in passed_rows),
        thresholds=thresholds,
    )


def _row_is_technical_pass(row: BatchWindowSummary) -> bool:
    if row.status == "failed":
        return False
    return not any(blocker in TECHNICAL_BLOCKERS for blocker in row.blockers)


def _read_metrics(path: Path) -> dict[str, float]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return {str(row["metric"]): float(str(row["value"])) for row in reader}


def _read_manifest(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _write_summary_csv(path: Path, rows: list[BatchWindowSummary]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    try:
        with temp_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=BATCH_SUMMARY_COLUMNS)
            writer.writeheader()
            for row in rows:
                writer.writerow(_csv_row(row))
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _write_summary_json(path: Path, summary: BatchExperimentSummary) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    try:
        temp_path.write_text(
            json.dumps(summary.model_dump(mode="json"), sort_keys=True, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _csv_row(row: BatchWindowSummary) -> dict[str, str | int | float | None]:
    return {
        "window_label": row.window_label,
        "start": _format_datetime(row.start),
        "end": _format_datetime(row.end),
        "status": row.status,
        "blockers": ";".join(row.blockers),
        "run_id": row.run_id,
        "dataset_hash": row.dataset_hash,
        "config_hash": row.config_hash,
        "bar_count": row.bar_count,
        "trade_count": row.trade_count,
        "net_profit": row.net_profit,
        "max_drawdown": row.max_drawdown,
        "profit_factor": row.profit_factor,
        "win_rate": row.win_rate,
        "sharpe_ratio": row.sharpe_ratio,
        "average_trade": row.average_trade,
        "expectancy": row.expectancy,
        "feed_gap_count": row.feed_gap_count,
        "context_timeframes_available": ";".join(row.context_timeframes_available),
        "downloaded_csv_paths_json": json.dumps(row.downloaded_csv_paths, sort_keys=True),
        "manifest_path": row.manifest_path,
        "artifact_dir": row.artifact_dir,
    }


def _validate_batch_inputs(*, symbol: str, windows: list[BatchWindow]) -> None:
    if symbol != "BTCUSDT":
        msg = "crypto batch runner is scoped to BTCUSDT only"
        raise ValueError(msg)
    if not windows:
        msg = "at least one batch window is required"
        raise ValueError(msg)
    labels = [window.label for window in windows]
    if len(labels) != len(set(labels)):
        msg = "batch window labels must be unique"
        raise ValueError(msg)
    for window in windows:
        start = to_utc(window.start)
        end = to_utc(window.end)
        if end <= start:
            msg = f"batch window end must be after start: {window.label}"
            raise ValueError(msg)


def _batch_id(*, windows: list[BatchWindow], thresholds: ResearchThresholds) -> str:
    payload = {
        "windows": [
            {"label": window.label, "start": _format_datetime(window.start), "end": _format_datetime(window.end)}
            for window in windows
        ],
        "thresholds": thresholds.model_dump(mode="json"),
        "symbol": "BTCUSDT",
        "source": "bybit_public",
        "execution_timeframe": "M15",
    }
    return stable_hash(payload).split(":", maxsplit=1)[1][:16]


def _format_datetime(value: datetime) -> str:
    return to_utc(value).isoformat().replace("+00:00", "Z")


def _optional_float(value: float | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _mean_optional(values: Iterable[float | None]) -> float | None:
    numbers = [float(value) for value in values if value is not None]
    if not numbers:
        return None
    return sum(numbers) / len(numbers)


def _min_optional(values: Iterable[float | None]) -> float | None:
    numbers = [float(value) for value in values if value is not None]
    if not numbers:
        return None
    return min(numbers)


def _resolve_windows(args: argparse.Namespace) -> list[BatchWindow]:
    selected = [bool(args.preset), bool(args.windows), bool(args.windows_file)]
    if sum(selected) != 1:
        msg = "provide exactly one of --preset, --windows, or --windows-file"
        raise ValueError(msg)
    if args.preset:
        return preset_windows(args.preset)
    if args.windows:
        return parse_windows(args.windows)
    return load_windows_file(args.windows_file)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run BTCUSDT public-data batch research experiments")
    parser.add_argument("--preset", choices=["quarterly-2023-2024"])
    parser.add_argument("--windows", help="Comma-separated label:start/end windows")
    parser.add_argument("--windows-file", help="JSON list of {label,start,end} windows")
    parser.add_argument("--output-dir", default="artifacts/batch-backtests")
    parser.add_argument("--market-data-dir", default="artifacts/batch-market-data")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--stop-on-error", action="store_true")
    parser.add_argument("--min-trade-count", type=int, default=1)
    parser.add_argument("--min-net-profit", type=float, default=0.0)
    parser.add_argument("--min-profit-factor", type=float, default=1.0)
    parser.add_argument("--min-max-drawdown", type=float, default=-0.35)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = run_batch_experiment(
        windows=_resolve_windows(args),
        output_dir=args.output_dir,
        market_data_dir=args.market_data_dir,
        thresholds=ResearchThresholds(
            min_trade_count=args.min_trade_count,
            min_net_profit=args.min_net_profit,
            min_profit_factor=args.min_profit_factor,
            min_max_drawdown=args.min_max_drawdown,
        ),
        symbol=args.symbol,
        continue_on_error=not args.stop_on_error,
    )
    print(json.dumps(result.summary.model_dump(mode="json"), sort_keys=True, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
