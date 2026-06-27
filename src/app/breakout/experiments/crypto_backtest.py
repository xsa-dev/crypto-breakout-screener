"""BTCUSDT public-data historical breakout experiment runner.

This module is deliberately local and read-only: it imports historical OHLCV rows
from an explicit CSV path or downloads public Bybit kline data, normalizes rows
into canonical bars, runs the existing BacktestEngine, and writes local research
artifacts. It does not read exchange credentials, account state, balances,
positions, or private endpoints.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

import aiohttp
from pydantic import BaseModel, Field

from src.app.breakout.backtesting import BacktestEngine, stable_hash
from src.app.breakout.experiments.crypto_symbols import (
    DEFAULT_CRYPTO_RESEARCH_SYMBOL,
    normalize_crypto_research_symbol,
)
from src.app.breakout.normalizer import Normalizer, to_utc
from src.core.enums import TimeFrame
from src.core.models import (
    BacktestConfig,
    BacktestConfirmationFilterConfig,
    BacktestCostModel,
    BacktestExitProfileConfig,
    BacktestFeatureFilterConfig,
    BacktestResearchGateConfig,
    BreakoutStrategyConfig,
    ScoreConfig,
)
from src.core.schemas import Bar, FeedGap

DEFAULT_CONTEXT_TIMEFRAMES = (TimeFrame.H1.value, TimeFrame.H4.value, TimeFrame.D1.value)
REQUIRED_DOWNLOAD_TIMEFRAMES = (
    TimeFrame.M15.value,
    TimeFrame.H1.value,
    TimeFrame.H4.value,
    TimeFrame.D1.value,
)
_BYBIT_INTERVAL_BY_TIMEFRAME = {
    TimeFrame.M15.value: "15",
    TimeFrame.H1.value: "60",
    TimeFrame.H4.value: "240",
    TimeFrame.D1.value: "D",
}
_TIMEFRAME_SECONDS = {
    TimeFrame.M15.value: 900,
    TimeFrame.H1.value: 3600,
    TimeFrame.H4.value: 14400,
    TimeFrame.D1.value: 86400,
}
_BYBIT_KLINE_URL = "https://api.bybit.com/v5/market/kline"
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
    source_metadata: dict[str, Any] = Field(default_factory=dict)


class PublicDownloadResult(BaseModel):
    """Public downloader output paths and provider diagnostics."""

    provider: Literal["bybit"] = "bybit"
    source: Literal["bybit_public"] = "bybit_public"
    category: Literal["linear"] = "linear"
    symbol: str
    requested_start: datetime
    requested_end: datetime
    csv_paths: dict[str, str]
    source_metadata: dict[str, Any]


class DatasetManifest(BaseModel):
    """Reproducibility manifest written alongside crypto backtest artifacts."""

    source: Literal["csv", "bybit_public"] = "csv"
    market: Literal["crypto"] = "crypto"
    instrument_type: Literal["perpetual", "futures"] = "perpetual"
    symbol: str
    timeframe: str
    requested_context_timeframes: list[str]
    available_context_timeframes: list[str]
    unavailable_context_timeframes: dict[str, str]
    context_dataset_paths: dict[str, str] = Field(default_factory=dict)
    start_ts: datetime
    end_ts: datetime
    bar_count: int
    dataset_hash: str
    feed_gaps: list[FeedGap]
    normalization_warnings: list[str]
    generated_at: datetime
    source_metadata: dict[str, Any]
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
    symbol: str = DEFAULT_CRYPTO_RESEARCH_SYMBOL,
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


async def download_bybit_public_ohlcv(
    *,
    start: datetime,
    end: datetime,
    output_dir: str | Path = "artifacts/market-data",
    symbol: str = DEFAULT_CRYPTO_RESEARCH_SYMBOL,
    timeframes: Sequence[str] = REQUIRED_DOWNLOAD_TIMEFRAMES,
    category: Literal["linear"] = "linear",
    limit: int = 1000,
    timeout_seconds: float = 10.0,
    max_retries: int = 2,
) -> PublicDownloadResult:
    """Download public Bybit OHLCV data for all required first-slice timeframes."""

    start_utc, end_utc = _validate_download_inputs(symbol=symbol, start=start, end=end)
    requested_timeframes = _validate_download_timeframes(timeframes)
    if not 1 <= limit <= 1000:
        msg = "limit must be between 1 and 1000"
        raise ValueError(msg)

    output_root = Path(output_dir)
    csv_paths: dict[str, str] = {}
    timeframe_metadata: dict[str, Any] = {}
    async with aiohttp.ClientSession() as session:
        for timeframe in requested_timeframes:
            rows, metadata = await _download_bybit_timeframe(
                session=session,
                category=category,
                symbol=symbol,
                timeframe=timeframe,
                start=start_utc,
                end=end_utc,
                limit=limit,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
            )
            csv_path = _download_csv_path(
                output_root=output_root,
                provider="bybit",
                category=category,
                symbol=symbol,
                timeframe=timeframe,
                start=start_utc,
                end=end_utc,
            )
            _write_ohlcv_csv_atomic(csv_path, rows)
            csv_paths[timeframe] = str(csv_path)
            timeframe_metadata[timeframe] = {**metadata, "csv_path": str(csv_path)}

    return PublicDownloadResult(
        symbol=symbol,
        requested_start=start_utc,
        requested_end=end_utc,
        csv_paths=csv_paths,
        source_metadata={
            "provider": "bybit",
            "source": "bybit_public",
            "endpoint": _BYBIT_KLINE_URL,
            "category": category,
            "symbol": symbol,
            "requested_start": start_utc.isoformat(),
            "requested_end": end_utc.isoformat(),
            "timeframes": list(requested_timeframes),
            "csv_paths": csv_paths,
            "timeframe_metadata": timeframe_metadata,
        },
    )


def download_bybit_public_ohlcv_sync(**kwargs: Any) -> PublicDownloadResult:
    """Synchronous wrapper for CLI/tests around the async public downloader."""

    return asyncio.run(download_bybit_public_ohlcv(**kwargs))


def run_crypto_experiment(
    *,
    csv_path: str | Path,
    output_dir: str | Path = "artifacts/backtests",
    symbol: str = DEFAULT_CRYPTO_RESEARCH_SYMBOL,
    timeframe: str = TimeFrame.M15.value,
    instrument_type: Literal["perpetual", "futures"] = "perpetual",
    source: Literal["csv", "bybit_public"] = "csv",
    context_csv_paths: dict[str, str] | None = None,
    source_metadata: dict[str, Any] | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    spread: float = 0.10,
    slippage: float = 0.02,
    commission_per_unit: float = 0.01,
    funding_per_bar: float = 0.0,
    commission_rate: float = 0.0,
    funding_rate_per_bar: float = 0.0,
    initial_equity: float = 10_000.0,
    base_quantity: float = 10.0,
    stop_distance: float = 2.0,
    min_warmup_bars: int = 7,
    random_seed: int = 42,
    research_gates: BacktestResearchGateConfig | None = None,
    feature_filters: BacktestFeatureFilterConfig | None = None,
    confirmation_filters: BacktestConfirmationFilterConfig | None = None,
    exit_profile: BacktestExitProfileConfig | None = None,
    forward_path_diagnostics: bool = False,
    path_risk_diagnostics: bool = False,
) -> CryptoExperimentResult:
    """Run an approved public crypto historical experiment and write local artifacts."""

    symbol = normalize_crypto_research_symbol(symbol)
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
            "source_metadata": {
                **imported.source_metadata,
                **(source_metadata or {}),
                "output_bars": len(bars),
            },
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
            commission_rate=commission_rate,
            funding_rate_per_bar=funding_rate_per_bar,
        ),
        research_gates=research_gates or BacktestResearchGateConfig(),
        feature_filters=feature_filters or BacktestFeatureFilterConfig(),
        confirmation_filters=confirmation_filters or BacktestConfirmationFilterConfig(),
        exit_profile=exit_profile or BacktestExitProfileConfig(),
        forward_path_diagnostics=forward_path_diagnostics,
        path_risk_diagnostics=path_risk_diagnostics,
        strategy=BreakoutStrategyConfig(
            symbols=[symbol],
            execution_timeframe=TimeFrame.M15,
            score=ScoreConfig(threshold_normal=30, threshold_reduced=10),
        ),
    )
    context_paths = context_csv_paths or {}
    context_bars = {
        context_timeframe: import_crypto_csv(
            context_path,
            symbol=symbol,
            timeframe=context_timeframe,
        ).bars
        for context_timeframe, context_path in context_paths.items()
    }
    engine = BacktestEngine(config, context_bars=context_bars)
    report = engine.run(bars)
    unavailable = dict(report.unavailable_reasons)
    if funding_per_bar == 0 and funding_rate_per_bar == 0:
        unavailable["funding"] = DEFAULT_LIMITATIONS["funding"]
    if context_paths:
        unavailable["context_timeframes"] = (
            "H1/H4/D1 are consumed by research feature diagnostics; M15 remains execution input"
        )
    else:
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
        source=source,
        context_csv_paths=context_paths,
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
    source: Literal["csv", "bybit_public"] = "csv",
    context_csv_paths: dict[str, str] | None = None,
    report_run_id: str,
    report_config_hash: str,
    report_artifact_paths: list[str],
) -> DatasetManifest:
    """Build the reproducibility manifest from normalized bars and report metadata."""

    context_paths = context_csv_paths or {}
    unavailable_context = {
        timeframe: "not supplied by first-slice M15 CSV input"
        for timeframe in DEFAULT_CONTEXT_TIMEFRAMES
        if timeframe not in context_paths
    }
    limitations = dict(DEFAULT_LIMITATIONS)
    if context_paths:
        limitations["context_timeframes"] = (
            "H1/H4/D1 were downloaded as context datasets; current backtest consumes M15 only"
        )
    return DatasetManifest(
        source=source,
        instrument_type=instrument_type,
        symbol=bars[0]["symbol"],
        timeframe=bars[0]["timeframe"],
        requested_context_timeframes=list(DEFAULT_CONTEXT_TIMEFRAMES),
        available_context_timeframes=sorted(context_paths),
        unavailable_context_timeframes=unavailable_context,
        context_dataset_paths=context_paths,
        start_ts=bars[0]["ts"],
        end_ts=bars[-1]["ts"],
        bar_count=len(bars),
        dataset_hash=stable_hash(bars),
        feed_gaps=imported.gaps,
        normalization_warnings=imported.warnings,
        generated_at=datetime.now(tz=UTC),
        source_metadata=imported.source_metadata,
        limitations=limitations,
        report_run_id=report_run_id,
        report_config_hash=report_config_hash,
        report_artifact_paths=report_artifact_paths,
    )


async def _download_bybit_timeframe(
    *,
    session: aiohttp.ClientSession,
    category: str,
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime,
    limit: int,
    timeout_seconds: float,
    max_retries: int,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    interval = _BYBIT_INTERVAL_BY_TIMEFRAME[timeframe]
    interval_ms = _TIMEFRAME_SECONDS[timeframe] * 1000
    start_ms = _to_milliseconds(start)
    end_ms = _to_milliseconds(end)
    page_start_ms = start_ms
    page_count = 0
    response_rows = 0
    by_timestamp: dict[int, dict[str, str]] = {}
    warnings: list[str] = []
    now_ms = _to_milliseconds(datetime.now(tz=UTC))

    while page_start_ms <= end_ms:
        page_end_ms = min(end_ms, page_start_ms + interval_ms * (limit - 1))
        payload = await _request_bybit_public_json(
            session=session,
            params={
                "category": category,
                "symbol": symbol,
                "interval": interval,
                "start": str(page_start_ms),
                "end": str(page_end_ms),
                "limit": str(limit),
            },
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )
        page_count += 1
        raw_rows = _extract_bybit_rows(payload)
        response_rows += len(raw_rows)
        for raw_row in raw_rows:
            timestamp_ms, row = _parse_bybit_kline_row(raw_row, timeframe=timeframe)
            if timestamp_ms < start_ms or timestamp_ms > end_ms:
                continue
            if timestamp_ms + interval_ms > now_ms:
                warnings.append(f"incomplete_latest_candle_excluded:{timeframe}:{timestamp_ms}")
                continue
            by_timestamp[timestamp_ms] = row
        page_start_ms = page_end_ms + interval_ms

    rows = [by_timestamp[timestamp] for timestamp in sorted(by_timestamp)]
    if not rows:
        msg = f"public Bybit download returned no closed rows for {symbol} {timeframe}"
        raise ValueError(msg)
    return rows, {
        "provider": "bybit",
        "source": "bybit_public",
        "endpoint": _BYBIT_KLINE_URL,
        "category": category,
        "symbol": symbol,
        "timeframe": timeframe,
        "interval": interval,
        "requested_start": start.isoformat(),
        "requested_end": end.isoformat(),
        "fetched_start": rows[0]["timestamp"],
        "fetched_end": rows[-1]["timestamp"],
        "page_count": page_count,
        "response_row_count": response_rows,
        "accepted_row_count": len(rows),
        "warnings": warnings,
    }


async def _request_bybit_public_json(
    *,
    session: aiohttp.ClientSession,
    params: dict[str, str],
    timeout_seconds: float,
    max_retries: int,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            async with session.get(
                _BYBIT_KLINE_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=timeout_seconds),
            ) as response:
                text = await response.text()
                if response.status != 200:
                    msg = f"Bybit public kline HTTP {response.status}: {text[:200]}"
                    raise RuntimeError(msg)
                payload = json.loads(text)
        except (aiohttp.ClientError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
            last_error = exc
            if attempt >= max_retries:
                break
            await asyncio.sleep(0.25 * (attempt + 1))
            continue
        ret_code = payload.get("retCode")
        if ret_code != 0:
            msg = f"Bybit public kline error retCode={ret_code}: {payload.get('retMsg')}"
            last_error = RuntimeError(msg)
            if attempt >= max_retries:
                break
            await asyncio.sleep(0.25 * (attempt + 1))
            continue
        return cast(dict[str, Any], payload)
    msg = f"Bybit public kline request failed after {max_retries + 1} attempts: {last_error}"
    raise RuntimeError(msg)


def _extract_bybit_rows(payload: dict[str, Any]) -> list[list[str]]:
    result = payload.get("result")
    if not isinstance(result, dict):
        msg = "Bybit public kline payload missing result object"
        raise ValueError(msg)
    rows = result.get("list")
    if not isinstance(rows, list):
        msg = "Bybit public kline payload missing result.list"
        raise ValueError(msg)
    normalized_rows: list[list[str]] = []
    for row in rows:
        if not isinstance(row, list) or len(row) < 6:
            msg = "Bybit public kline row is malformed"
            raise ValueError(msg)
        normalized_rows.append([str(item) for item in row])
    return normalized_rows


def _parse_bybit_kline_row(row: list[str], *, timeframe: str) -> tuple[int, dict[str, str]]:
    timestamp_ms = int(row[0])
    timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC)
    return timestamp_ms, {
        "timestamp": _format_utc_z(timestamp),
        "open": str(float(row[1])),
        "high": str(float(row[2])),
        "low": str(float(row[3])),
        "close": str(float(row[4])),
        "volume": str(float(row[5])),
        "source": f"bybit_public:{timeframe}",
    }


def _write_ohlcv_csv_atomic(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    try:
        with temp_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=["timestamp", "open", "high", "low", "close", "volume", "source"],
            )
            writer.writeheader()
            writer.writerows(rows)
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _download_csv_path(
    *,
    output_root: Path,
    provider: str,
    category: str,
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime,
) -> Path:
    return (
        output_root
        / provider
        / category
        / symbol
        / timeframe
        / f"{_path_timestamp(start)}_{_path_timestamp(end)}.csv"
    )


def _validate_download_inputs(
    *, symbol: str, start: datetime, end: datetime
) -> tuple[datetime, datetime]:
    normalize_crypto_research_symbol(symbol)
    start_utc = to_utc(start)
    end_utc = to_utc(end)
    if end_utc <= start_utc:
        msg = "download end must be after start"
        raise ValueError(msg)
    return start_utc, end_utc


def _validate_download_timeframes(timeframes: Sequence[str]) -> tuple[str, ...]:
    requested = tuple(dict.fromkeys(timeframes))
    if set(requested) != set(REQUIRED_DOWNLOAD_TIMEFRAMES):
        msg = "public downloader requires M15,H1,H4,D1 timeframes"
        raise ValueError(msg)
    return tuple(timeframe for timeframe in REQUIRED_DOWNLOAD_TIMEFRAMES if timeframe in requested)


def _to_milliseconds(value: datetime) -> int:
    return int(to_utc(value).timestamp() * 1000)


def _format_utc_z(value: datetime) -> str:
    return to_utc(value).isoformat().replace("+00:00", "Z")


def _path_timestamp(value: datetime) -> str:
    return _format_utc_z(value).replace(":", "").replace("-", "").replace("Z", "Z")


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
        "source": row.get("source") or source,
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


def _parse_required_datetime(value: str | None, *, name: str) -> datetime:
    parsed = _parse_optional_datetime(value)
    if parsed is None:
        msg = f"--{name} is required for public downloads"
        raise ValueError(msg)
    return parsed


def _parse_timeframes(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the BTCUSDT M15 crypto backtest experiment")
    parser.add_argument("--csv", help="Public OHLCV CSV path")
    parser.add_argument("--output-dir", default="artifacts/backtests")
    parser.add_argument("--market-data-dir", default="artifacts/market-data")
    parser.add_argument("--download-public", choices=["bybit"])
    parser.add_argument("--download-only", action="store_true")
    parser.add_argument("--download-limit", type=int, default=1000)
    parser.add_argument("--timeframes", default=",".join(REQUIRED_DOWNLOAD_TIMEFRAMES))
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--timeframe", default=TimeFrame.M15.value)
    parser.add_argument("--instrument-type", choices=["perpetual", "futures"], default="perpetual")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--spread", type=float, default=0.10)
    parser.add_argument("--slippage", type=float, default=0.02)
    parser.add_argument("--commission-per-unit", type=float, default=0.01)
    parser.add_argument("--funding-per-bar", type=float, default=0.0)
    parser.add_argument("--commission-rate", type=float, default=0.0)
    parser.add_argument("--funding-rate-per-bar", type=float, default=0.0)
    parser.add_argument("--initial-equity", type=float, default=10_000.0)
    parser.add_argument("--base-quantity", type=float, default=10.0)
    parser.add_argument("--stop-distance", type=float, default=2.0)
    parser.add_argument("--min-warmup-bars", type=int, default=7)
    parser.add_argument("--random-seed", type=int, default=42)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    csv_path = args.csv
    context_csv_paths: dict[str, str] = {}
    source: Literal["csv", "bybit_public"] = "csv"
    source_metadata: dict[str, Any] | None = None
    if args.download_public:
        start = _parse_required_datetime(args.start, name="start")
        end = _parse_required_datetime(args.end, name="end")
        download = download_bybit_public_ohlcv_sync(
            start=start,
            end=end,
            output_dir=args.market_data_dir,
            symbol=args.symbol,
            timeframes=_parse_timeframes(args.timeframes),
            limit=args.download_limit,
        )
        if args.download_only:
            print(
                json.dumps(
                    {
                        "source": download.source,
                        "symbol": download.symbol,
                        "requested_start": download.requested_start.isoformat(),
                        "requested_end": download.requested_end.isoformat(),
                        "csv_paths": download.csv_paths,
                        "source_metadata": download.source_metadata,
                    },
                    sort_keys=True,
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 0
        csv_path = download.csv_paths[TimeFrame.M15.value]
        context_csv_paths = {
            timeframe: path
            for timeframe, path in download.csv_paths.items()
            if timeframe != TimeFrame.M15.value
        }
        source = "bybit_public"
        source_metadata = download.source_metadata
    if csv_path is None:
        msg = "--csv is required unless --download-public is used"
        raise ValueError(msg)
    result = run_crypto_experiment(
        csv_path=csv_path,
        output_dir=args.output_dir,
        symbol=args.symbol,
        timeframe=args.timeframe,
        instrument_type=args.instrument_type,
        source=source,
        context_csv_paths=context_csv_paths,
        source_metadata=source_metadata,
        start=_parse_optional_datetime(args.start) if not args.download_public else None,
        end=_parse_optional_datetime(args.end) if not args.download_public else None,
        spread=args.spread,
        slippage=args.slippage,
        commission_per_unit=args.commission_per_unit,
        funding_per_bar=args.funding_per_bar,
        commission_rate=args.commission_rate,
        funding_rate_per_bar=args.funding_rate_per_bar,
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
