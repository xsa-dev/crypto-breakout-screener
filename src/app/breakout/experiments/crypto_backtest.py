"""BTCUSDT public-data historical breakout experiment runner.

This module is deliberately local and read-only: it imports historical OHLCV rows
from an explicit CSV path, normalizes them into canonical bars, runs the existing
BacktestEngine, and writes local research artifacts. It does not read exchange
credentials, account state, balances, positions, or private endpoints.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, Field

from src.app.breakout.backtesting import BacktestEngine, stable_hash
from src.app.breakout.normalizer import Normalizer, to_utc
from src.core.enums import TimeFrame
from src.core.models import BacktestConfig, BacktestCostModel, BreakoutStrategyConfig, ScoreConfig
from src.core.schemas import Bar, FeedGap

DEFAULT_CONTEXT_TIMEFRAMES = (TimeFrame.H1.value, TimeFrame.H4.value, TimeFrame.D1.value)
DEFAULT_LIMITATIONS = {
    "funding": "funding is not modeled in the first BTCUSDT fixture/public-data experiment",
    "context_timeframes": "H1/H4/D1 are recorded as requested metadata only in the first slice",
    "order_book_density": "order-book density is unavailable for CSV OHLCV research input",
    "production_approval": "research artifact only; not production OOS or live-trading approval",
}


class CsvImportResult(BaseModel):
    """Normalized CSV import payload with diagnostics for the dataset manifest."""

    bars: list[Bar]
    gaps: list[FeedGap] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source_metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class DatasetManifest(BaseModel):
    """Reproducibility manifest written alongside crypto backtest artifacts."""

    source: Literal["csv"] = "csv"
    market: Literal["crypto"] = "crypto"
    instrument_type: Literal["perpetual", "futures"] = "perpetual"
    symbol: str
    timeframe: str
    requested_context_timeframes: list[str]
    available_context_timeframes: list[str]
    unavailable_context_timeframes: dict[str, str]
    start_ts: datetime
    end_ts: datetime
    bar_count: int
    dataset_hash: str
    feed_gaps: list[FeedGap]
    normalization_warnings: list[str]
    generated_at: datetime
    source_metadata: dict[str, str | int | float | bool]
    limitations: dict[str, str]
    report_run_id: str
    report_config_hash: str
    report_artifact_paths: list[str]


@dataclass(frozen=True)
class CryptoExperimentResult:
    """Result returned by the runner for tests and CLI summary printing."""

    run_id: str
    symbol: str
    timeframe: str
    bar_count: int
    dataset_hash: str
    config_hash: str
    trade_count: int
    net_pnl: float
    max_drawdown: float
    win_rate: float
    artifact_dir: Path
    manifest_path: Path
    artifact_paths: list[str]


def import_crypto_csv(
    path: str | Path,
    *,
    symbol: str = "BTCUSDT",
    timeframe: str = TimeFrame.M15.value,
) -> CsvImportResult:
    """Import public OHLCV CSV rows into canonical Bars with deterministic diagnostics."""

    csv_path = Path(path)
    normalizer = Normalizer()
    raw_bars: list[Bar] = []
    warnings: list[str] = []
    input_timestamps: list[datetime] = []

    with csv_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row_number, row in enumerate(reader, start=2):
            raw = _csv_row_to_raw_bar(row, row_number=row_number, source=csv_path.name)
            bar = normalizer.normalize_bar(raw, symbol=symbol, timeframe=timeframe)
            _validate_ohlc(bar, row_number=row_number)
            raw_bars.append(bar)
            input_timestamps.append(bar["ts"])

    if not raw_bars:
        msg = f"CSV file contains no bars: {csv_path}"
        raise ValueError(msg)

    duplicates = len(raw_bars) - len({(bar["symbol"], bar["timeframe"], bar["ts"]) for bar in raw_bars})
    if duplicates:
        warnings.append(f"duplicate_bars_last_row_wins:{duplicates}")

    if input_timestamps != sorted(input_timestamps):
        warnings.append("input_rows_out_of_order_sorted")

    bars = normalizer.deduplicate_bars(raw_bars)
    gaps = normalizer.detect_bar_gaps(bars)
    return CsvImportResult(
        bars=bars,
        gaps=gaps,
        warnings=warnings,
        source_metadata={
            "path": str(csv_path),
            "file_name": csv_path.name,
            "input_rows": len(raw_bars),
            "accepted_bars": len(bars),
        },
    )


def run_crypto_experiment(
    *,
    csv_path: str | Path,
    output_dir: str | Path = "artifacts/backtests",
    symbol: str = "BTCUSDT",
    timeframe: str = TimeFrame.M15.value,
    instrument_type: Literal["perpetual", "futures"] = "perpetual",
    start: datetime | None = None,
    end: datetime | None = None,
    spread: float = 0.10,
    slippage: float = 0.02,
    commission_per_unit: float = 0.01,
    funding_per_bar: float = 0.0,
    initial_equity: float = 10_000.0,
    base_quantity: float = 10.0,
    stop_distance: float = 2.0,
    min_warmup_bars: int = 7,
    random_seed: int = 42,
) -> CryptoExperimentResult:
    """Run the first BTCUSDT crypto historical experiment and write local artifacts."""

    if symbol != "BTCUSDT":
        msg = "first crypto historical experiment is scoped to BTCUSDT only"
        raise ValueError(msg)
    if timeframe != TimeFrame.M15.value:
        msg = "first crypto historical experiment is scoped to M15 only"
        raise ValueError(msg)

    imported = import_crypto_csv(csv_path, symbol=symbol, timeframe=timeframe)
    bars = _filter_date_range(imported.bars, start=start, end=end)
    if not bars:
        msg = "no bars remain after applying the requested date range"
        raise ValueError(msg)
    manifest_import = imported.model_copy(
        update={
            "gaps": Normalizer().detect_bar_gaps(bars),
            "source_metadata": {**imported.source_metadata, "output_bars": len(bars)},
        }
    )

    config = BacktestConfig(
        initial_equity=initial_equity,
        base_quantity=base_quantity,
        stop_distance=stop_distance,
        min_warmup_bars=min_warmup_bars,
        random_seed=random_seed,
        cost_model=BacktestCostModel(
            spread=spread,
            commission_per_unit=commission_per_unit,
            slippage_per_unit=slippage,
            funding_per_bar=funding_per_bar,
        ),
        strategy=BreakoutStrategyConfig(
            symbols=[symbol],
            execution_timeframe=TimeFrame.M15,
            score=ScoreConfig(threshold_normal=30, threshold_reduced=10),
        ),
    )
    engine = BacktestEngine(config)
    report = engine.run(bars)
    unavailable = dict(report.unavailable_reasons)
    if funding_per_bar == 0:
        unavailable["funding"] = DEFAULT_LIMITATIONS["funding"]
    unavailable["context_timeframes"] = DEFAULT_LIMITATIONS["context_timeframes"]
    unavailable["order_book_density"] = DEFAULT_LIMITATIONS["order_book_density"]
    unavailable["production_approval"] = DEFAULT_LIMITATIONS["production_approval"]
    report = report.model_copy(update={"unavailable_reasons": unavailable})

    artifact_dir = Path(output_dir) / "crypto" / symbol / report.run_id
    exported = engine.export_report(report, artifact_dir)
    manifest_path = artifact_dir / f"{report.run_id}-dataset-manifest.json"
    artifact_paths = [*exported.artifact_paths, str(manifest_path)]
    manifest = build_dataset_manifest(
        imported=manifest_import,
        bars=bars,
        instrument_type=instrument_type,
        report_run_id=report.run_id,
        report_config_hash=report.config_hash,
        report_artifact_paths=artifact_paths,
    )
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), sort_keys=True, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    exported = exported.model_copy(update={"artifact_paths": artifact_paths})
    _rewrite_report_json(exported, artifact_dir)

    return CryptoExperimentResult(
        run_id=report.run_id,
        symbol=symbol,
        timeframe=timeframe,
        bar_count=len(bars),
        dataset_hash=report.dataset_hash,
        config_hash=report.config_hash,
        trade_count=int(_metric_number(report.metrics["trade_count"])),
        net_pnl=_metric_number(report.metrics["net_profit"]),
        max_drawdown=_metric_number(report.metrics["max_drawdown"]),
        win_rate=_metric_number(report.metrics["win_rate"]),
        artifact_dir=artifact_dir,
        manifest_path=manifest_path,
        artifact_paths=artifact_paths,
    )


def build_dataset_manifest(
    *,
    imported: CsvImportResult,
    bars: list[Bar],
    instrument_type: Literal["perpetual", "futures"],
    report_run_id: str,
    report_config_hash: str,
    report_artifact_paths: list[str],
) -> DatasetManifest:
    """Build the reproducibility manifest from normalized bars and report metadata."""

    return DatasetManifest(
        instrument_type=instrument_type,
        symbol=bars[0]["symbol"],
        timeframe=bars[0]["timeframe"],
        requested_context_timeframes=list(DEFAULT_CONTEXT_TIMEFRAMES),
        available_context_timeframes=[],
        unavailable_context_timeframes={
            timeframe: "not supplied by first-slice M15 CSV input"
            for timeframe in DEFAULT_CONTEXT_TIMEFRAMES
        },
        start_ts=bars[0]["ts"],
        end_ts=bars[-1]["ts"],
        bar_count=len(bars),
        dataset_hash=stable_hash(bars),
        feed_gaps=imported.gaps,
        normalization_warnings=imported.warnings,
        generated_at=datetime.now(tz=UTC),
        source_metadata=imported.source_metadata,
        limitations=dict(DEFAULT_LIMITATIONS),
        report_run_id=report_run_id,
        report_config_hash=report_config_hash,
        report_artifact_paths=report_artifact_paths,
    )


def _csv_row_to_raw_bar(
    row: dict[str, str],
    *,
    row_number: int,
    source: str,
) -> dict[str, Any]:
    timestamp_value = row.get("ts") or row.get("timestamp") or row.get("time")
    if not timestamp_value:
        msg = f"row {row_number}: missing ts/timestamp/time"
        raise ValueError(msg)
    raw: dict[str, Any] = {
        "ts": _parse_timestamp(timestamp_value),
        "open": _required_float(row, "open", row_number=row_number),
        "high": _required_float(row, "high", row_number=row_number),
        "low": _required_float(row, "low", row_number=row_number),
        "close": _required_float(row, "close", row_number=row_number),
        "volume": _required_float(row, "volume", row_number=row_number),
        "source": source,
    }
    if row.get("spread"):
        raw["spread"] = _required_float(row, "spread", row_number=row_number)
    return raw


def _parse_timestamp(value: str) -> datetime | int | float:
    text = value.strip()
    try:
        numeric = float(text)
    except ValueError:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return to_utc(parsed)
    if numeric > 10_000_000_000:
        numeric = numeric / 1000
    return numeric


def _required_float(row: dict[str, str], field: str, *, row_number: int) -> float:
    value = row.get(field)
    if value is None or value == "":
        msg = f"row {row_number}: missing {field}"
        raise ValueError(msg)
    return float(value)


def _validate_ohlc(bar: Bar, *, row_number: int) -> None:
    if bar["high"] < max(bar["open"], bar["close"], bar["low"]):
        msg = f"row {row_number}: high is below open/close/low"
        raise ValueError(msg)
    if bar["low"] > min(bar["open"], bar["close"], bar["high"]):
        msg = f"row {row_number}: low is above open/close/high"
        raise ValueError(msg)


def _filter_date_range(
    bars: list[Bar], *, start: datetime | None, end: datetime | None
) -> list[Bar]:
    start_utc = to_utc(start) if start is not None else None
    end_utc = to_utc(end) if end is not None else None
    return [
        bar
        for bar in bars
        if (start_utc is None or bar["ts"] >= start_utc)
        and (end_utc is None or bar["ts"] <= end_utc)
    ]


def _metric_number(value: float | int | str | None) -> float:
    if value is None:
        msg = "required numeric report metric is unavailable"
        raise ValueError(msg)
    return float(cast(float | int | str, value))


def _rewrite_report_json(report: Any, artifact_dir: Path) -> None:
    report_path = artifact_dir / f"{report.run_id}.json"
    report_path.write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _parse_optional_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = _parse_timestamp(value)
    return to_utc(parsed)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the BTCUSDT M15 crypto backtest experiment")
    parser.add_argument("--csv", required=True, help="Public OHLCV CSV path")
    parser.add_argument("--output-dir", default="artifacts/backtests")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--timeframe", default=TimeFrame.M15.value)
    parser.add_argument("--instrument-type", choices=["perpetual", "futures"], default="perpetual")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--spread", type=float, default=0.10)
    parser.add_argument("--slippage", type=float, default=0.02)
    parser.add_argument("--commission-per-unit", type=float, default=0.01)
    parser.add_argument("--funding-per-bar", type=float, default=0.0)
    parser.add_argument("--initial-equity", type=float, default=10_000.0)
    parser.add_argument("--base-quantity", type=float, default=10.0)
    parser.add_argument("--stop-distance", type=float, default=2.0)
    parser.add_argument("--min-warmup-bars", type=int, default=7)
    parser.add_argument("--random-seed", type=int, default=42)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = run_crypto_experiment(
        csv_path=args.csv,
        output_dir=args.output_dir,
        symbol=args.symbol,
        timeframe=args.timeframe,
        instrument_type=args.instrument_type,
        start=_parse_optional_datetime(args.start),
        end=_parse_optional_datetime(args.end),
        spread=args.spread,
        slippage=args.slippage,
        commission_per_unit=args.commission_per_unit,
        funding_per_bar=args.funding_per_bar,
        initial_equity=args.initial_equity,
        base_quantity=args.base_quantity,
        stop_distance=args.stop_distance,
        min_warmup_bars=args.min_warmup_bars,
        random_seed=args.random_seed,
    )
    summary = {
        "run_id": result.run_id,
        "symbol": result.symbol,
        "timeframe": result.timeframe,
        "bar_count": result.bar_count,
        "dataset_hash": result.dataset_hash,
        "config_hash": result.config_hash,
        "trade_count": result.trade_count,
        "net_pnl": result.net_pnl,
        "max_drawdown": result.max_drawdown,
        "win_rate": result.win_rate,
        "artifact_dir": str(result.artifact_dir),
        "dataset_manifest": str(result.manifest_path),
        "artifact_paths": result.artifact_paths,
    }
    print(json.dumps(summary, sort_keys=True, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
