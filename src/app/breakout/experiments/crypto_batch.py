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
import statistics
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
from src.core.models import (
    BacktestConfirmationFilterConfig,
    BacktestExitProfileConfig,
    BacktestFeatureFilterConfig,
    BacktestResearchGateConfig,
)

BATCH_SUMMARY_COLUMNS = [
    "window_label",
    "start",
    "end",
    "gate_profile",
    "feature_filter_profile",
    "risk_control_profile",
    "regime_filter_profile",
    "confirmation_filter_profile",
    "exit_profile",
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
    "gate_settings_json",
    "feature_filter_settings_json",
    "feature_filter_skip_counts_json",
    "risk_control_settings_json",
    "risk_control_skip_counts_json",
    "regime_filter_settings_json",
    "regime_filter_skip_counts_json",
    "confirmation_filter_settings_json",
    "confirmation_filter_skip_counts_json",
    "exit_profile_settings_json",
    "exit_profile_counts_json",
    "cost_model_settings_json",
    "feature_artifact_paths_json",
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
    gate_profile: str = "baseline"
    feature_filter_profile: str = "none"
    risk_control_profile: str = "none"
    regime_filter_profile: str = "none"
    confirmation_filter_profile: str = "none"
    exit_profile: str = "none"
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
    gate_settings: dict[str, Any] = Field(default_factory=dict)
    feature_filter_settings: dict[str, Any] = Field(default_factory=dict)
    feature_filter_skip_counts: dict[str, int] = Field(default_factory=dict)
    risk_control_settings: dict[str, Any] = Field(default_factory=dict)
    risk_control_skip_counts: dict[str, int] = Field(default_factory=dict)
    regime_filter_settings: dict[str, Any] = Field(default_factory=dict)
    regime_filter_skip_counts: dict[str, int] = Field(default_factory=dict)
    confirmation_filter_settings: dict[str, Any] = Field(default_factory=dict)
    confirmation_filter_skip_counts: dict[str, int] = Field(default_factory=dict)
    exit_profile_settings: dict[str, Any] = Field(default_factory=dict)
    exit_profile_counts: dict[str, int] = Field(default_factory=dict)
    cost_model_settings: dict[str, Any] = Field(default_factory=dict)
    feature_artifact_paths: dict[str, str] = Field(default_factory=dict)
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
    gate_profile: str = "baseline"
    feature_filter_profile: str = "none"
    risk_control_profile: str = "none"
    regime_filter_profile: str = "none"
    confirmation_filter_profile: str = "none"
    exit_profile: str = "none"
    gate_settings: dict[str, Any] = Field(default_factory=dict)
    feature_filter_settings: dict[str, Any] = Field(default_factory=dict)
    risk_control_settings: dict[str, Any] = Field(default_factory=dict)
    regime_filter_settings: dict[str, Any] = Field(default_factory=dict)
    confirmation_filter_settings: dict[str, Any] = Field(default_factory=dict)
    exit_profile_settings: dict[str, Any] = Field(default_factory=dict)
    cost_model_settings: dict[str, Any] = Field(default_factory=dict)
    context_timeframes: list[str] = Field(default_factory=lambda: ["H1", "H4", "D1"])
    windows: list[BatchWindowSummary]
    aggregate: BatchAggregate
    bad_regime_diagnostics_enabled: bool = False
    forward_path_diagnostics_enabled: bool = False
    path_risk_diagnostics_enabled: bool = False
    diagnostic_artifact_paths: dict[str, str] = Field(default_factory=dict)
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

EXIT_PROFILE_NAMES = {
    "conservative-v1-m15-slope-positive-max-trades-8-hold-2",
    "conservative-v1-m15-slope-positive-max-trades-8-hold-4",
    "conservative-v1-m15-slope-positive-max-trades-8-hold-8",
    "conservative-v1-m15-slope-positive-max-trades-8-hold-16",
    "conservative-v1-m15-slope-positive-max-trades-8-hold-32",
    "conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p01-target-2p0",
    "conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p25-target-2p0-hold-8",
    "conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p5-target-2p0-hold-8",
    "conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p75-target-2p5-hold-16",
    "conservative-v1-m15-slope-positive-max-trades-8-atr-stop-1p0-target-1p5",
    "conservative-v1-m15-slope-positive-max-trades-8-atr-stop-1p5-target-2p0",
    "conservative-v1-m15-slope-positive-max-trades-8-breakeven-1p0-hold-8",
    "conservative-v1-m15-slope-positive-max-trades-8-close-stop-0p5-close-target-2p0-hold-16",
    "conservative-v1-m15-slope-positive-max-trades-8-close-stop-0p5-hold-8",
    "conservative-v1-m15-slope-positive-max-trades-8-close-stop-1p0-hold-16",
    "conservative-v1-m15-slope-positive-max-trades-8-trail-1p0-giveback-0p5-hold-8",
    "conservative-v1-m15-slope-positive-max-trades-8-trail-1p0-giveback-1p0-hold-16",
}


def research_gate_profile(name: str) -> BacktestResearchGateConfig:
    """Return named local research gates for overtrading comparison runs."""

    if name == "baseline":
        return BacktestResearchGateConfig()
    if name in {
        "conservative-v1",
        "conservative-v1-m15-slope-positive",
        "conservative-v1-h1-long",
        "conservative-v1-m15-slope-positive-h1-long",
        "conservative-v1-m15-slope-positive-body-cap",
        "conservative-v1-m15-slope-positive-daily-stop-3000",
        "conservative-v1-m15-slope-positive-daily-stop-2000",
        "conservative-v1-m15-slope-positive-max-trades-8",
        "conservative-v1-m15-slope-positive-max-trades-8-atr25-block",
        "conservative-v1-m15-slope-positive-max-trades-8-atr25-breakout1-block",
        "conservative-v1-m15-slope-positive-max-trades-8-atr25-body75-block",
        "conservative-v1-m15-slope-positive-max-trades-8-atr25-body25-75-block",
        "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1",
        "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-2",
        "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-closepos70",
        "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-no-return-inside-range",
        "conservative-v1-m15-slope-positive-loss-cooldown-12",
        *EXIT_PROFILE_NAMES,
    }:
        daily_stop_loss = 5_000.0
        max_trades_per_day = 12
        cooldown_bars_after_loss = 6
        if name == "conservative-v1-m15-slope-positive-daily-stop-3000":
            daily_stop_loss = 3_000.0
        elif name == "conservative-v1-m15-slope-positive-daily-stop-2000":
            daily_stop_loss = 2_000.0
        elif name.startswith("conservative-v1-m15-slope-positive-max-trades-8"):
            max_trades_per_day = 8
        elif name == "conservative-v1-m15-slope-positive-loss-cooldown-12":
            cooldown_bars_after_loss = 12
        return BacktestResearchGateConfig(
            min_entry_score=40,
            cooldown_bars_after_trade=3,
            cooldown_bars_after_loss=cooldown_bars_after_loss,
            block_immediate_reentry=True,
            max_trades_per_day=max_trades_per_day,
            daily_stop_loss=daily_stop_loss,
        )
    msg = f"unsupported gate profile: {name}"
    raise ValueError(msg)


def feature_filter_profile(name: str) -> BacktestFeatureFilterConfig:
    """Return named local feature filters for research comparison runs."""

    if name in {"baseline", "conservative-v1", "none"}:
        return BacktestFeatureFilterConfig()
    if name == "conservative-v1-m15-slope-positive-max-trades-8-atr25-block":
        return BacktestFeatureFilterConfig(
            require_m15_ema_slope_positive=True,
            min_atr_percentile=0.25,
        )
    if name == "conservative-v1-m15-slope-positive-max-trades-8-atr25-breakout1-block":
        return BacktestFeatureFilterConfig(
            require_m15_ema_slope_positive=True,
            min_atr_percentile=0.25,
            max_breakout_distance_atr=1.0,
        )
    if name == "conservative-v1-m15-slope-positive-max-trades-8-atr25-body75-block":
        return BacktestFeatureFilterConfig(
            require_m15_ema_slope_positive=True,
            min_atr_percentile=0.25,
            max_candle_body_ratio=0.75,
        )
    if name == "conservative-v1-m15-slope-positive-max-trades-8-atr25-body25-75-block":
        return BacktestFeatureFilterConfig(
            require_m15_ema_slope_positive=True,
            min_atr_percentile=0.25,
            min_candle_body_ratio=0.25,
            max_candle_body_ratio=0.75,
        )
    if name in {
        "conservative-v1-m15-slope-positive",
        "conservative-v1-m15-slope-positive-daily-stop-3000",
        "conservative-v1-m15-slope-positive-daily-stop-2000",
        "conservative-v1-m15-slope-positive-max-trades-8",
        "conservative-v1-m15-slope-positive-max-trades-8-atr25-block",
        "conservative-v1-m15-slope-positive-max-trades-8-atr25-breakout1-block",
        "conservative-v1-m15-slope-positive-max-trades-8-atr25-body75-block",
        "conservative-v1-m15-slope-positive-max-trades-8-atr25-body25-75-block",
        "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1",
        "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-2",
        "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-closepos70",
        "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-no-return-inside-range",
        "conservative-v1-m15-slope-positive-loss-cooldown-12",
        *EXIT_PROFILE_NAMES,
    }:
        return BacktestFeatureFilterConfig(require_m15_ema_slope_positive=True)
    if name == "conservative-v1-h1-long":
        return BacktestFeatureFilterConfig(require_h1_trend_long=True)
    if name == "conservative-v1-m15-slope-positive-h1-long":
        return BacktestFeatureFilterConfig(
            require_m15_ema_slope_positive=True,
            require_h1_trend_long=True,
        )
    if name == "conservative-v1-m15-slope-positive-body-cap":
        return BacktestFeatureFilterConfig(
            require_m15_ema_slope_positive=True,
            max_candle_body_ratio=0.75,
        )
    msg = f"unsupported feature filter profile: {name}"
    raise ValueError(msg)


def _feature_filter_profile_name(gate_profile: str, explicit: str | None = None) -> str:
    if explicit is not None:
        return explicit
    if gate_profile in {
        "conservative-v1-m15-slope-positive",
        "conservative-v1-h1-long",
        "conservative-v1-m15-slope-positive-h1-long",
        "conservative-v1-m15-slope-positive-body-cap",
        "conservative-v1-m15-slope-positive-daily-stop-3000",
        "conservative-v1-m15-slope-positive-daily-stop-2000",
        "conservative-v1-m15-slope-positive-max-trades-8",
        "conservative-v1-m15-slope-positive-max-trades-8-atr25-block",
        "conservative-v1-m15-slope-positive-max-trades-8-atr25-breakout1-block",
        "conservative-v1-m15-slope-positive-max-trades-8-atr25-body75-block",
        "conservative-v1-m15-slope-positive-max-trades-8-atr25-body25-75-block",
        "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1",
        "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-2",
        "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-closepos70",
        "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-no-return-inside-range",
        "conservative-v1-m15-slope-positive-loss-cooldown-12",
        *EXIT_PROFILE_NAMES,
    }:
        if gate_profile.startswith("conservative-v1-m15-slope-positive-"):
            return "conservative-v1-m15-slope-positive"
        return gate_profile
    return "none"


def _risk_control_profile_name(gate_profile: str) -> str:
    if gate_profile.startswith("conservative-v1-m15-slope-positive-max-trades-8"):
        return "conservative-v1-m15-slope-positive-max-trades-8"
    if gate_profile in {
        "conservative-v1-m15-slope-positive-daily-stop-3000",
        "conservative-v1-m15-slope-positive-daily-stop-2000",
        "conservative-v1-m15-slope-positive-loss-cooldown-12",
        *EXIT_PROFILE_NAMES,
    }:
        return gate_profile
    return "none"


def _regime_filter_profile_name(gate_profile: str) -> str:
    if gate_profile in {
        "conservative-v1-m15-slope-positive-max-trades-8-atr25-block",
        "conservative-v1-m15-slope-positive-max-trades-8-atr25-breakout1-block",
        "conservative-v1-m15-slope-positive-max-trades-8-atr25-body75-block",
        "conservative-v1-m15-slope-positive-max-trades-8-atr25-body25-75-block",
    }:
        return gate_profile
    return "none"


def _regime_filter_settings(config: BacktestFeatureFilterConfig) -> dict[str, Any]:
    return {
        key: value
        for key, value in config.model_dump(mode="json").items()
        if key in {
            "min_atr_percentile",
            "max_breakout_distance_atr",
            "min_candle_body_ratio",
            "max_candle_body_ratio",
        }
        and value is not None
    }


def confirmation_filter_profile(name: str) -> BacktestConfirmationFilterConfig:
    """Return named local confirmation filters for false-breakout comparison runs."""

    if name in {"baseline", "conservative-v1", "none"}:
        return BacktestConfirmationFilterConfig()
    if name == "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1":
        return BacktestConfirmationFilterConfig(required_closes_above_breakout=1)
    if name == "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-2":
        return BacktestConfirmationFilterConfig(required_closes_above_breakout=2)
    if name == "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-closepos70":
        return BacktestConfirmationFilterConfig(
            required_closes_above_breakout=1,
            min_close_position=0.70,
        )
    if name == "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-no-return-inside-range":
        return BacktestConfirmationFilterConfig(
            required_closes_above_breakout=1,
            cancel_on_return_inside_range=True,
        )
    return BacktestConfirmationFilterConfig()


def _confirmation_filter_profile_name(gate_profile: str) -> str:
    if gate_profile in {
        "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1",
        "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-2",
        "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-closepos70",
        "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-no-return-inside-range",
    }:
        return gate_profile
    return "none"


def exit_profile_config(name: str) -> BacktestExitProfileConfig:
    """Return named local exit profiles for path-risk comparison runs."""

    if name in {"baseline", "conservative-v1", "none"}:
        return BacktestExitProfileConfig()
    if name == "conservative-v1-m15-slope-positive-max-trades-8-hold-2":
        return BacktestExitProfileConfig(fixed_holding_bars=2)
    if name == "conservative-v1-m15-slope-positive-max-trades-8-hold-4":
        return BacktestExitProfileConfig(fixed_holding_bars=4)
    if name == "conservative-v1-m15-slope-positive-max-trades-8-hold-8":
        return BacktestExitProfileConfig(fixed_holding_bars=8)
    if name == "conservative-v1-m15-slope-positive-max-trades-8-hold-16":
        return BacktestExitProfileConfig(fixed_holding_bars=16)
    if name == "conservative-v1-m15-slope-positive-max-trades-8-hold-32":
        return BacktestExitProfileConfig(fixed_holding_bars=32)
    if name == "conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p01-target-2p0":
        return BacktestExitProfileConfig(fixed_holding_bars=1, stop_atr=0.01, target_atr=2.0)
    if name == "conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p25-target-2p0-hold-8":
        return BacktestExitProfileConfig(fixed_holding_bars=8, stop_atr=0.25, target_atr=2.0)
    if name == "conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p5-target-2p0-hold-8":
        return BacktestExitProfileConfig(fixed_holding_bars=8, stop_atr=0.5, target_atr=2.0)
    if name == "conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p75-target-2p5-hold-16":
        return BacktestExitProfileConfig(fixed_holding_bars=16, stop_atr=0.75, target_atr=2.5)
    if name == "conservative-v1-m15-slope-positive-max-trades-8-atr-stop-1p0-target-1p5":
        return BacktestExitProfileConfig(fixed_holding_bars=4, stop_atr=1.0, target_atr=1.5)
    if name == "conservative-v1-m15-slope-positive-max-trades-8-atr-stop-1p5-target-2p0":
        return BacktestExitProfileConfig(fixed_holding_bars=8, stop_atr=1.5, target_atr=2.0)
    if name == "conservative-v1-m15-slope-positive-max-trades-8-breakeven-1p0-hold-8":
        return BacktestExitProfileConfig(fixed_holding_bars=8, breakeven_after_atr=1.0)
    if name == "conservative-v1-m15-slope-positive-max-trades-8-close-stop-0p5-hold-8":
        return BacktestExitProfileConfig(fixed_holding_bars=8, close_stop_atr=0.5)
    if name == "conservative-v1-m15-slope-positive-max-trades-8-close-stop-1p0-hold-16":
        return BacktestExitProfileConfig(fixed_holding_bars=16, close_stop_atr=1.0)
    if name == "conservative-v1-m15-slope-positive-max-trades-8-close-stop-0p5-close-target-2p0-hold-16":
        return BacktestExitProfileConfig(
            fixed_holding_bars=16,
            close_stop_atr=0.5,
            close_target_atr=2.0,
        )
    if name == "conservative-v1-m15-slope-positive-max-trades-8-trail-1p0-giveback-0p5-hold-8":
        return BacktestExitProfileConfig(
            fixed_holding_bars=8,
            trailing_after_atr=1.0,
            trailing_giveback_atr=0.5,
        )
    if name == "conservative-v1-m15-slope-positive-max-trades-8-trail-1p0-giveback-1p0-hold-16":
        return BacktestExitProfileConfig(
            fixed_holding_bars=16,
            trailing_after_atr=1.0,
            trailing_giveback_atr=1.0,
        )
    return BacktestExitProfileConfig()


def _exit_profile_name(gate_profile: str) -> str:
    if gate_profile in EXIT_PROFILE_NAMES:
        return gate_profile
    return "none"


def run_batch_experiment(
    *,
    windows: list[BatchWindow],
    output_dir: str | Path = "artifacts/batch-backtests",
    market_data_dir: str | Path = "artifacts/batch-market-data",
    thresholds: ResearchThresholds | None = None,
    gate_profile: str = "baseline",
    research_gates: BacktestResearchGateConfig | None = None,
    feature_filter_profile_name: str | None = None,
    feature_filters: BacktestFeatureFilterConfig | None = None,
    confirmation_filters: BacktestConfirmationFilterConfig | None = None,
    enable_bad_regime_diagnostics: bool = False,
    enable_forward_path_diagnostics: bool = False,
    enable_path_risk_diagnostics: bool = False,
    reuse_market_data: bool = False,
    spread: float = 0.10,
    slippage: float = 0.02,
    commission_per_unit: float = 0.01,
    funding_per_bar: float = 0.0,
    commission_rate: float = 0.0,
    funding_rate_per_bar: float = 0.0,
    symbol: str = "BTCUSDT",
    continue_on_error: bool = True,
    download: DownloadCallable = download_bybit_public_ohlcv_sync,
    run_single: RunCallable = run_crypto_experiment,
) -> BatchExperimentResult:
    """Run BTCUSDT public-data research experiments over multiple windows."""

    _validate_batch_inputs(symbol=symbol, windows=windows)
    active_thresholds = thresholds or ResearchThresholds()
    active_feature_filter_profile = _feature_filter_profile_name(
        gate_profile,
        feature_filter_profile_name,
    )
    active_risk_control_profile = _risk_control_profile_name(gate_profile)
    active_regime_filter_profile = _regime_filter_profile_name(gate_profile)
    active_confirmation_filter_profile = _confirmation_filter_profile_name(gate_profile)
    active_exit_profile = _exit_profile_name(gate_profile)
    active_gates = research_gates or research_gate_profile(gate_profile)
    active_feature_filters = feature_filters or feature_filter_profile(
        gate_profile if active_regime_filter_profile != "none" else active_feature_filter_profile
    )
    gate_settings = active_gates.model_dump(mode="json")
    feature_filter_settings = active_feature_filters.model_dump(mode="json")
    risk_control_settings = gate_settings if active_risk_control_profile != "none" else {}
    regime_filter_settings = (
        _regime_filter_settings(active_feature_filters)
        if active_regime_filter_profile != "none"
        else {}
    )
    active_confirmation_filters = confirmation_filters or confirmation_filter_profile(
        active_confirmation_filter_profile
    )
    confirmation_filter_settings = (
        active_confirmation_filters.model_dump(mode="json")
        if active_confirmation_filter_profile != "none"
        else {}
    )
    active_exit_config = exit_profile_config(active_exit_profile)
    exit_profile_settings = (
        active_exit_config.model_dump(mode="json", exclude_none=True)
        if active_exit_profile != "none"
        else {}
    )
    cost_model_settings = _cost_model_settings(
        spread=spread,
        slippage=slippage,
        commission_per_unit=commission_per_unit,
        funding_per_bar=funding_per_bar,
        commission_rate=commission_rate,
        funding_rate_per_bar=funding_rate_per_bar,
    )
    batch_id = _batch_id(
        windows=windows,
        thresholds=active_thresholds,
        gate_profile=gate_profile,
        gate_settings=gate_settings,
        feature_filter_profile=active_feature_filter_profile,
        feature_filter_settings=feature_filter_settings,
        risk_control_profile=active_risk_control_profile,
        risk_control_settings=risk_control_settings,
        regime_filter_profile=active_regime_filter_profile,
        regime_filter_settings=regime_filter_settings,
        confirmation_filter_profile=active_confirmation_filter_profile,
        confirmation_filter_settings=confirmation_filter_settings,
        exit_profile=active_exit_profile,
        exit_profile_settings=exit_profile_settings,
        cost_model_settings=cost_model_settings,
        bad_regime_diagnostics_enabled=enable_bad_regime_diagnostics,
        forward_path_diagnostics_enabled=enable_forward_path_diagnostics,
        path_risk_diagnostics_enabled=enable_path_risk_diagnostics,
    )
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
                gate_profile=gate_profile,
                feature_filter_profile=active_feature_filter_profile,
                risk_control_profile=active_risk_control_profile,
                regime_filter_profile=active_regime_filter_profile,
                confirmation_filter_profile=active_confirmation_filter_profile,
                exit_profile=active_exit_profile,
                research_gates=active_gates,
                feature_filters=active_feature_filters,
                confirmation_filters=active_confirmation_filters,
                exit_profile_config=active_exit_config,
                cost_model_settings=cost_model_settings,
                reuse_market_data=reuse_market_data,
                spread=spread,
                slippage=slippage,
                commission_per_unit=commission_per_unit,
                funding_per_bar=funding_per_bar,
                commission_rate=commission_rate,
                funding_rate_per_bar=funding_rate_per_bar,
                forward_path_diagnostics=enable_forward_path_diagnostics,
                path_risk_diagnostics=enable_path_risk_diagnostics,
                download=download,
                run_single=run_single,
            )
        except Exception as exc:  # noqa: BLE001 - batch summaries must record failed windows.
            row = BatchWindowSummary(
                window_label=window.label,
                start=to_utc(window.start),
                end=to_utc(window.end),
                gate_profile=gate_profile,
                feature_filter_profile=active_feature_filter_profile,
                risk_control_profile=active_risk_control_profile,
                regime_filter_profile=active_regime_filter_profile,
                confirmation_filter_profile=active_confirmation_filter_profile,
                exit_profile=active_exit_profile,
                gate_settings=gate_settings,
                feature_filter_settings=feature_filter_settings,
                risk_control_settings=risk_control_settings,
                regime_filter_settings=regime_filter_settings,
                confirmation_filter_settings=confirmation_filter_settings,
                exit_profile_settings=exit_profile_settings,
                cost_model_settings=cost_model_settings,
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
    diagnostic_paths = (
        _write_bad_regime_diagnostics(
            artifact_dir=artifact_dir,
            rows=rows,
            gate_profile=gate_profile,
            thresholds=active_thresholds,
        )
        if enable_bad_regime_diagnostics
        else {}
    )
    if enable_forward_path_diagnostics:
        diagnostic_paths.update(_write_forward_path_batch_diagnostics(artifact_dir=artifact_dir, rows=rows))
    if enable_path_risk_diagnostics:
        diagnostic_paths.update(_write_path_risk_batch_diagnostics(artifact_dir=artifact_dir, rows=rows))
    summary = BatchExperimentSummary(
        batch_id=batch_id,
        gate_profile=gate_profile,
        feature_filter_profile=active_feature_filter_profile,
        risk_control_profile=active_risk_control_profile,
        regime_filter_profile=active_regime_filter_profile,
        confirmation_filter_profile=active_confirmation_filter_profile,
        exit_profile=active_exit_profile,
        gate_settings=gate_settings,
        feature_filter_settings=feature_filter_settings,
        risk_control_settings=risk_control_settings,
        regime_filter_settings=regime_filter_settings,
        confirmation_filter_settings=confirmation_filter_settings,
        exit_profile_settings=exit_profile_settings,
        cost_model_settings=cost_model_settings,
        windows=rows,
        aggregate=aggregate,
        bad_regime_diagnostics_enabled=enable_bad_regime_diagnostics,
        forward_path_diagnostics_enabled=enable_forward_path_diagnostics,
        path_risk_diagnostics_enabled=enable_path_risk_diagnostics,
        diagnostic_artifact_paths=diagnostic_paths,
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
    gate_profile: str,
    feature_filter_profile: str,
    risk_control_profile: str,
    regime_filter_profile: str,
    confirmation_filter_profile: str,
    exit_profile: str,
    research_gates: BacktestResearchGateConfig,
    feature_filters: BacktestFeatureFilterConfig,
    confirmation_filters: BacktestConfirmationFilterConfig,
    exit_profile_config: BacktestExitProfileConfig,
    cost_model_settings: dict[str, Any],
    reuse_market_data: bool,
    spread: float,
    slippage: float,
    commission_per_unit: float,
    funding_per_bar: float,
    commission_rate: float,
    funding_rate_per_bar: float,
    forward_path_diagnostics: bool,
    path_risk_diagnostics: bool,
    download: DownloadCallable,
    run_single: RunCallable,
) -> BatchWindowSummary:
    start = to_utc(window.start)
    end = to_utc(window.end)
    downloaded = (
        _cached_public_download(
            start=start,
            end=end,
            market_data_dir=market_data_dir,
            symbol=symbol,
        )
        if reuse_market_data
        else download(
            start=start,
            end=end,
            output_dir=market_data_dir,
            symbol=symbol,
        )
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
        research_gates=research_gates,
        feature_filters=feature_filters,
        confirmation_filters=confirmation_filters,
        exit_profile=exit_profile_config,
        spread=spread,
        slippage=slippage,
        commission_per_unit=commission_per_unit,
        funding_per_bar=funding_per_bar,
        commission_rate=commission_rate,
        funding_rate_per_bar=funding_rate_per_bar,
        forward_path_diagnostics=forward_path_diagnostics,
        path_risk_diagnostics=path_risk_diagnostics,
    )
    metrics = _read_metrics(result.artifact_dir / f"{result.run_id}-metrics.csv")
    manifest = _read_manifest(result.manifest_path)
    feed_gap_count = len(cast(list[Any], manifest.get("feed_gaps", [])))
    available_context = [str(item) for item in manifest.get("available_context_timeframes", [])]
    row = BatchWindowSummary(
        window_label=window.label,
        start=start,
        end=end,
        gate_profile=gate_profile,
        feature_filter_profile=feature_filter_profile,
        risk_control_profile=risk_control_profile,
        regime_filter_profile=regime_filter_profile,
        confirmation_filter_profile=confirmation_filter_profile,
        exit_profile=exit_profile,
        gate_settings=research_gates.model_dump(mode="json"),
        feature_filter_settings=feature_filters.model_dump(mode="json"),
        feature_filter_skip_counts=_feature_filter_skip_counts(result.artifact_dir / f"{result.run_id}-parameters.json"),
        risk_control_settings=research_gates.model_dump(mode="json") if risk_control_profile != "none" else {},
        risk_control_skip_counts=_risk_control_skip_counts(result.artifact_dir / f"{result.run_id}-parameters.json"),
        regime_filter_settings=_regime_filter_settings(feature_filters) if regime_filter_profile != "none" else {},
        regime_filter_skip_counts=_regime_filter_skip_counts(result.artifact_dir / f"{result.run_id}-parameters.json"),
        confirmation_filter_settings=confirmation_filters.model_dump(mode="json") if confirmation_filter_profile != "none" else {},
        confirmation_filter_skip_counts=_confirmation_filter_skip_counts(result.artifact_dir / f"{result.run_id}-parameters.json"),
        exit_profile_settings=exit_profile_config.model_dump(mode="json", exclude_none=True)
        if exit_profile != "none"
        else {},
        exit_profile_counts=_exit_profile_counts(result.artifact_dir / f"{result.run_id}-parameters.json"),
        cost_model_settings=cost_model_settings,
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
        feature_artifact_paths=_feature_artifact_paths(result.artifact_paths),
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


def _feature_filter_skip_counts(path: Path) -> dict[str, int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_counts = payload.get("research_gate_skip_counts", {})
    if not isinstance(raw_counts, dict):
        return {}
    feature_reasons = {
        "skipped_feature_m15_ema_slope_not_positive",
        "skipped_feature_h1_trend_not_long",
    }
    return {
        str(key): int(value)
        for key, value in raw_counts.items()
        if str(key) in feature_reasons and isinstance(value, int | float)
    }


def _risk_control_skip_counts(path: Path) -> dict[str, int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_counts = payload.get("research_gate_skip_counts", {})
    if not isinstance(raw_counts, dict):
        return {}
    risk_reasons = {
        "skipped_daily_stop_loss",
        "skipped_max_trades_per_day",
        "skipped_cooldown",
    }
    return {
        str(key): int(value)
        for key, value in raw_counts.items()
        if str(key) in risk_reasons and isinstance(value, int | float)
    }


def _regime_filter_skip_counts(path: Path) -> dict[str, int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_counts = payload.get("research_gate_skip_counts", {})
    if not isinstance(raw_counts, dict):
        return {}
    regime_reasons = {
        "skipped_feature_atr_percentile_unavailable",
        "skipped_feature_atr_percentile_below_min",
        "skipped_feature_breakout_distance_atr_unavailable",
        "skipped_feature_breakout_distance_atr_above_cap",
        "skipped_feature_candle_body_ratio_unavailable",
        "skipped_feature_candle_body_ratio_below_min",
        "skipped_feature_candle_body_ratio_above_cap",
    }
    return {
        str(key): int(value)
        for key, value in raw_counts.items()
        if str(key) in regime_reasons and isinstance(value, int | float)
    }


def _confirmation_filter_skip_counts(path: Path) -> dict[str, int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_counts = payload.get("research_gate_skip_counts", {})
    if not isinstance(raw_counts, dict):
        return {}
    return {
        str(key): int(value)
        for key, value in raw_counts.items()
        if str(key).startswith("skipped_confirmation_") and isinstance(value, int | float)
    }


def _exit_profile_counts(path: Path) -> dict[str, int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_counts = payload.get("exit_profile_counts", {})
    if not isinstance(raw_counts, dict):
        return {}
    return {
        str(key): int(value)
        for key, value in raw_counts.items()
        if isinstance(value, int | float)
    }


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


def _write_csv_rows(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    try:
        with temp_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _write_bad_regime_diagnostics(
    *,
    artifact_dir: Path,
    rows: list[BatchWindowSummary],
    gate_profile: str,
    thresholds: ResearchThresholds,
) -> dict[str, str]:
    failed_rows = [row for row in rows if row.status != "passed" and row.artifact_dir is not None]
    paths = {
        "failed_window_diagnostics": artifact_dir / "failed-window-diagnostics.csv",
        "worst_drawdown_runs": artifact_dir / "worst-drawdown-runs.csv",
        "bad_regime_bucket_summary": artifact_dir / "bad-regime-bucket-summary.csv",
    }
    _write_csv_rows(
        paths["failed_window_diagnostics"],
        [
            "window_label",
            "profile",
            "run_id",
            "status",
            "blockers",
            "failure_class",
            "trade_count",
            "net_profit",
            "max_drawdown",
            "profit_factor",
            "threshold_min_net_profit",
            "threshold_min_profit_factor",
            "threshold_min_max_drawdown",
            "artifact_dir",
        ],
        [_failed_window_diagnostic_row(row, gate_profile=gate_profile, thresholds=thresholds) for row in failed_rows],
    )
    _write_csv_rows(
        paths["worst_drawdown_runs"],
        [
            "window_label",
            "profile",
            "run_id",
            "min_drawdown",
            "min_drawdown_timestamp",
            "worst_negative_day",
            "worst_negative_day_net_pnl",
            "worst_negative_day_trade_count",
            "profitable_but_drawdown_blocked",
            "negative_expectancy_window",
            "source_drawdown_path",
            "source_worst_day_path",
        ],
        [_worst_drawdown_row(row, gate_profile=gate_profile) for row in failed_rows],
    )
    _write_csv_rows(
        paths["bad_regime_bucket_summary"],
        [
            "window_label",
            "profile",
            "run_id",
            "bucket_source",
            "diagnostic_dimension",
            "bucket",
            "trade_count",
            "net_pnl",
            "average_trade",
            "win_rate",
            "profit_factor",
            "no_lookahead_source",
        ],
        _bad_regime_bucket_rows(failed_rows, gate_profile=gate_profile),
    )
    return {key: str(path) for key, path in paths.items()}


def _write_forward_path_batch_diagnostics(
    *,
    artifact_dir: Path,
    rows: list[BatchWindowSummary],
) -> dict[str, str]:
    paths = {
        "forward_path_window_summary": artifact_dir / "forward-path-window-summary.csv",
        "passed_vs_failed_forward_path_summary": artifact_dir / "passed-vs-failed-forward-path-summary.csv",
    }
    _write_csv_rows(
        paths["forward_path_window_summary"],
        [
            "window_label",
            "status",
            "blockers",
            "run_id",
            "horizon_bars",
            "trade_count",
            "available_count",
            "unavailable_count",
            "synthetic_net_pnl",
            "average_forward_return",
            "average_mfe",
            "average_mae",
            "positive_forward_return_ratio",
        ],
        _forward_path_window_rows(rows),
    )
    _write_csv_rows(
        paths["passed_vs_failed_forward_path_summary"],
        [
            "window_group",
            "horizon_bars",
            "trade_count",
            "average_forward_return",
            "median_forward_return",
            "average_mfe",
            "median_mfe",
            "average_mae",
            "median_mae",
            "positive_forward_return_ratio",
            "returned_to_breakout_level_ratio",
            "crossed_below_entry_ratio",
        ],
        _passed_vs_failed_forward_path_rows(rows),
    )
    return {key: str(path) for key, path in paths.items()}


def _forward_path_window_rows(rows: list[BatchWindowSummary]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        path = row.feature_artifact_paths.get("holding_horizon_pnl")
        if not path:
            continue
        for item in _read_csv_dicts(Path(path)):
            enriched: dict[str, object] = {
                "window_label": row.window_label,
                "status": row.status,
                "blockers": ";".join(row.blockers),
                "run_id": row.run_id or "unavailable",
            }
            summary_item = {
                "horizon_bars": item.get("horizon_bars", "unavailable"),
                "trade_count": item.get("trade_count", "unavailable"),
                "available_count": item.get("available_count", "unavailable"),
                "unavailable_count": item.get("unavailable_count", "unavailable"),
                "synthetic_net_pnl": item.get("synthetic_net_pnl", "unavailable"),
                "average_forward_return": item.get("average_forward_return", "unavailable"),
                "average_mfe": item.get("average_mfe", "unavailable"),
                "average_mae": item.get("average_mae", "unavailable"),
                "positive_forward_return_ratio": item.get("positive_forward_return_ratio", "unavailable"),
            }
            enriched.update(summary_item)
            output.append(enriched)
    return output


def _passed_vs_failed_forward_path_rows(rows: list[BatchWindowSummary]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, int], list[dict[str, str]]] = {}
    for row in rows:
        path = row.feature_artifact_paths.get("forward_path_diagnostics")
        if not path:
            continue
        group = "passed" if row.status == "passed" else "failed"
        for item in _read_csv_dicts(Path(path)):
            if item.get("available") != "True":
                continue
            horizon = _optional_int(item.get("horizon_bars"))
            if horizon is None:
                continue
            grouped.setdefault((group, horizon), []).append(item)
    output: list[dict[str, object]] = []
    for (group, horizon), items in sorted(grouped.items()):
        output.append(
            {
                "window_group": group,
                "horizon_bars": horizon,
                "trade_count": len(items),
                "average_forward_return": _mean_csv_number(items, "forward_return"),
                "median_forward_return": _median_csv_number(items, "forward_return"),
                "average_mfe": _mean_csv_number(items, "mfe"),
                "median_mfe": _median_csv_number(items, "mfe"),
                "average_mae": _mean_csv_number(items, "mae"),
                "median_mae": _median_csv_number(items, "mae"),
                "positive_forward_return_ratio": _csv_true_ratio(items, "close_above_entry"),
                "returned_to_breakout_level_ratio": _csv_true_ratio(items, "returned_to_breakout_level"),
                "crossed_below_entry_ratio": _csv_true_ratio(items, "crossed_below_entry"),
            }
        )
    return output



def _write_path_risk_batch_diagnostics(
    *,
    artifact_dir: Path,
    rows: list[BatchWindowSummary],
) -> dict[str, str]:
    paths = {
        "path_risk_window_summary": artifact_dir / "path-risk-window-summary.csv",
        "passed_vs_failed_path_risk_summary": artifact_dir / "passed-vs-failed-path-risk-summary.csv",
    }
    _write_csv_rows(
        paths["path_risk_window_summary"],
        [
            "window_label",
            "status",
            "blockers",
            "run_id",
            "horizon_bars",
            "trade_count",
            "available_count",
            "unavailable_count",
            "average_max_favorable_atr",
            "median_max_favorable_atr",
            "average_max_adverse_atr",
            "median_max_adverse_atr",
            "breakeven_reachable_ratio",
            "breakeven_touched_after_reach_ratio",
        ],
        _path_risk_window_rows(rows),
    )
    _write_csv_rows(
        paths["passed_vs_failed_path_risk_summary"],
        [
            "window_group",
            "horizon_bars",
            "trade_count",
            "average_max_favorable_atr",
            "median_max_favorable_atr",
            "average_max_adverse_atr",
            "median_max_adverse_atr",
            "breakeven_reachable_ratio",
            "breakeven_touched_after_reach_ratio",
            "fav_1p0_before_adv_1p0_ratio",
            "adv_1p0_before_fav_1p0_ratio",
            "trail_after_fav_1p0_giveback_0p5_touched_ratio",
            "trail_after_fav_1p0_giveback_1p0_touched_ratio",
        ],
        _passed_vs_failed_path_risk_rows(rows),
    )
    return {key: str(path) for key, path in paths.items()}


def _path_risk_window_rows(rows: list[BatchWindowSummary]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        path = row.feature_artifact_paths.get("path_risk_threshold_summary")
        if not path:
            continue
        for item in _read_csv_dicts(Path(path)):
            enriched: dict[str, object] = {
                "window_label": row.window_label,
                "status": row.status,
                "blockers": ";".join(row.blockers),
                "run_id": row.run_id or "unavailable",
                "horizon_bars": item.get("horizon_bars", "unavailable"),
                "trade_count": item.get("trade_count", "unavailable"),
                "available_count": item.get("available_count", "unavailable"),
                "unavailable_count": item.get("unavailable_count", "unavailable"),
                "average_max_favorable_atr": item.get("average_max_favorable_atr", "unavailable"),
                "median_max_favorable_atr": item.get("median_max_favorable_atr", "unavailable"),
                "average_max_adverse_atr": item.get("average_max_adverse_atr", "unavailable"),
                "median_max_adverse_atr": item.get("median_max_adverse_atr", "unavailable"),
                "breakeven_reachable_ratio": item.get("breakeven_reachable_ratio", "unavailable"),
                "breakeven_touched_after_reach_ratio": item.get("breakeven_touched_after_reach_ratio", "unavailable"),
            }
            output.append(enriched)
    return output


def _passed_vs_failed_path_risk_rows(rows: list[BatchWindowSummary]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, int], list[dict[str, str]]] = {}
    for row in rows:
        path = row.feature_artifact_paths.get("path_risk_diagnostics")
        if not path:
            continue
        group = "passed" if row.status == "passed" else "failed"
        for item in _read_csv_dicts(Path(path)):
            if item.get("available") != "True":
                continue
            horizon = _optional_int(item.get("horizon_bars"))
            if horizon is None:
                continue
            grouped.setdefault((group, horizon), []).append(item)
    output: list[dict[str, object]] = []
    for (group, horizon), items in sorted(grouped.items()):
        output.append(
            {
                "window_group": group,
                "horizon_bars": horizon,
                "trade_count": len(items),
                "average_max_favorable_atr": _mean_csv_number(items, "max_favorable_atr"),
                "median_max_favorable_atr": _median_csv_number(items, "max_favorable_atr"),
                "average_max_adverse_atr": _mean_csv_number(items, "max_adverse_atr"),
                "median_max_adverse_atr": _median_csv_number(items, "max_adverse_atr"),
                "breakeven_reachable_ratio": _csv_true_ratio(items, "breakeven_reachable"),
                "breakeven_touched_after_reach_ratio": _csv_true_ratio(items, "breakeven_touched_after_reach"),
                "fav_1p0_before_adv_1p0_ratio": _csv_true_ratio(items, "fav_1p0_before_adv_1p0"),
                "adv_1p0_before_fav_1p0_ratio": _csv_true_ratio(items, "adv_1p0_before_fav_1p0"),
                "trail_after_fav_1p0_giveback_0p5_touched_ratio": _csv_true_ratio(items, "trail_after_fav_1p0_giveback_0p5_touched"),
                "trail_after_fav_1p0_giveback_1p0_touched_ratio": _csv_true_ratio(items, "trail_after_fav_1p0_giveback_1p0_touched"),
            }
        )
    return output


def _csv_numbers(rows: list[dict[str, str]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = _optional_float(row.get(key))
        if value is not None:
            values.append(value)
    return values


def _mean_csv_number(rows: list[dict[str, str]], key: str) -> float | str:
    values = _csv_numbers(rows, key)
    return sum(values) / len(values) if values else "unavailable"


def _median_csv_number(rows: list[dict[str, str]], key: str) -> float | str:
    values = _csv_numbers(rows, key)
    return statistics.median(values) if values else "unavailable"


def _csv_true_ratio(rows: list[dict[str, str]], key: str) -> float | str:
    values = [row.get(key) for row in rows if row.get(key) in {"True", "False"}]
    return sum(1 for value in values if value == "True") / len(values) if values else "unavailable"


def _optional_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _failed_window_diagnostic_row(
    row: BatchWindowSummary,
    *,
    gate_profile: str,
    thresholds: ResearchThresholds,
) -> dict[str, object]:
    return {
        "window_label": row.window_label,
        "profile": gate_profile,
        "run_id": row.run_id or "unavailable",
        "status": row.status,
        "blockers": ";".join(row.blockers),
        "failure_class": _failure_class(row),
        "trade_count": row.trade_count if row.trade_count is not None else "unavailable",
        "net_profit": row.net_profit if row.net_profit is not None else "unavailable",
        "max_drawdown": row.max_drawdown if row.max_drawdown is not None else "unavailable",
        "profit_factor": row.profit_factor if row.profit_factor is not None else "unavailable",
        "threshold_min_net_profit": thresholds.min_net_profit,
        "threshold_min_profit_factor": thresholds.min_profit_factor,
        "threshold_min_max_drawdown": thresholds.min_max_drawdown,
        "artifact_dir": row.artifact_dir or "unavailable",
    }


def _failure_class(row: BatchWindowSummary) -> str:
    if row.net_profit is not None and row.net_profit > 0 and row.profit_factor is not None and row.profit_factor > 1:
        if "max_drawdown_below_threshold" in row.blockers:
            return "profitable_drawdown_blocked"
    if row.net_profit is not None and row.net_profit <= 0:
        return "negative_or_flat_expectancy"
    if row.profit_factor is not None and row.profit_factor <= 1:
        return "profit_factor_blocked"
    if "max_drawdown_below_threshold" in row.blockers:
        return "drawdown_blocked"
    return "other_blocked"


def _worst_drawdown_row(row: BatchWindowSummary, *, gate_profile: str) -> dict[str, object]:
    artifact_dir = Path(row.artifact_dir) if row.artifact_dir else None
    drawdown_path = artifact_dir / f"{row.run_id}-drawdown.csv" if artifact_dir and row.run_id else None
    worst_day_path = (
        Path(row.feature_artifact_paths["worst_day_attribution"])
        if "worst_day_attribution" in row.feature_artifact_paths
        else None
    )
    min_drawdown, min_timestamp = _min_drawdown_point(drawdown_path)
    worst_day = _worst_negative_day(worst_day_path)
    return {
        "window_label": row.window_label,
        "profile": gate_profile,
        "run_id": row.run_id or "unavailable",
        "min_drawdown": min_drawdown,
        "min_drawdown_timestamp": min_timestamp,
        "worst_negative_day": worst_day.get("day", "unavailable"),
        "worst_negative_day_net_pnl": worst_day.get("net_pnl", "unavailable"),
        "worst_negative_day_trade_count": worst_day.get("trade_count", "unavailable"),
        "profitable_but_drawdown_blocked": _failure_class(row) == "profitable_drawdown_blocked",
        "negative_expectancy_window": row.net_profit is not None and row.net_profit <= 0,
        "source_drawdown_path": str(drawdown_path) if drawdown_path else "unavailable",
        "source_worst_day_path": str(worst_day_path) if worst_day_path else "unavailable",
    }


def _bad_regime_bucket_rows(rows: list[BatchWindowSummary], *, gate_profile: str) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        output.extend(_feature_bucket_diagnostic_rows(row, gate_profile=gate_profile))
        output.extend(_regime_bucket_diagnostic_rows(row, gate_profile=gate_profile))
    return sorted(
        output,
        key=lambda item: (
            str(item["window_label"]),
            str(item["bucket_source"]),
            str(item["diagnostic_dimension"]),
            str(item["bucket"]),
        ),
    )


def _feature_bucket_diagnostic_rows(row: BatchWindowSummary, *, gate_profile: str) -> list[dict[str, object]]:
    path = row.feature_artifact_paths.get("feature_bucket_pnl")
    if path is None:
        return []
    output: list[dict[str, object]] = []
    for source_row in _read_csv_dicts(Path(path)):
        output.append(
            {
                "window_label": row.window_label,
                "profile": gate_profile,
                "run_id": row.run_id or "unavailable",
                "bucket_source": "feature_bucket_pnl",
                "diagnostic_dimension": source_row.get("feature", "unavailable"),
                "bucket": source_row.get("bucket", "unavailable"),
                "trade_count": source_row.get("trade_count", "unavailable"),
                "net_pnl": source_row.get("net_pnl", "unavailable"),
                "average_trade": source_row.get("average_trade", "unavailable"),
                "win_rate": source_row.get("win_rate", "unavailable"),
                "profit_factor": source_row.get("profit_factor", "unavailable"),
                "no_lookahead_source": "entry_feature_snapshot",
            }
        )
    return output


def _regime_bucket_diagnostic_rows(row: BatchWindowSummary, *, gate_profile: str) -> list[dict[str, object]]:
    path = row.feature_artifact_paths.get("regime_bucket_summary")
    if path is None:
        return []
    output: list[dict[str, object]] = []
    for source_row in _read_csv_dicts(Path(path)):
        output.append(
            {
                "window_label": row.window_label,
                "profile": gate_profile,
                "run_id": row.run_id or "unavailable",
                "bucket_source": "regime_bucket_summary",
                "diagnostic_dimension": "combined_regime",
                "bucket": source_row.get("regime", "unavailable"),
                "trade_count": source_row.get("trade_count", "unavailable"),
                "net_pnl": source_row.get("net_pnl", "unavailable"),
                "average_trade": source_row.get("average_trade", "unavailable"),
                "win_rate": source_row.get("win_rate", "unavailable"),
                "profit_factor": source_row.get("profit_factor", "unavailable"),
                "no_lookahead_source": "entry_feature_snapshot",
            }
        )
    return output


def _min_drawdown_point(path: Path | None) -> tuple[float | str, str]:
    if path is None or not path.exists():
        return "unavailable", "unavailable"
    min_value: float | None = None
    min_timestamp = "unavailable"
    for row in _read_csv_dicts(path):
        value = _parse_optional_float(row.get("drawdown"))
        if value is None:
            continue
        if min_value is None or value < min_value:
            min_value = value
            min_timestamp = str(row.get("timestamp", "unavailable"))
    return (min_value, min_timestamp) if min_value is not None else ("unavailable", "unavailable")


def _worst_negative_day(path: Path | None) -> dict[str, object]:
    if path is None or not path.exists():
        return {}
    worst: dict[str, object] = {}
    worst_pnl: float | None = None
    for row in _read_csv_dicts(path):
        net_pnl = _parse_optional_float(row.get("net_pnl"))
        if net_pnl is None:
            continue
        if worst_pnl is None or net_pnl < worst_pnl:
            worst_pnl = net_pnl
            worst = {
                "day": row.get("day", "unavailable"),
                "net_pnl": net_pnl,
                "trade_count": row.get("trade_count", "unavailable"),
            }
    return worst


def _read_csv_dicts(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return [dict(row) for row in csv.DictReader(file)]


def _parse_optional_float(value: object) -> float | None:
    if value in {None, "", "unavailable"}:
        return None
    try:
        return float(str(value))
    except ValueError:
        return None


def _csv_row(row: BatchWindowSummary) -> dict[str, str | int | float | None]:
    return {
        "window_label": row.window_label,
        "start": _format_datetime(row.start),
        "end": _format_datetime(row.end),
        "gate_profile": row.gate_profile,
        "feature_filter_profile": row.feature_filter_profile,
        "risk_control_profile": row.risk_control_profile,
        "regime_filter_profile": row.regime_filter_profile,
        "confirmation_filter_profile": row.confirmation_filter_profile,
        "exit_profile": row.exit_profile,
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
        "gate_settings_json": json.dumps(row.gate_settings, sort_keys=True),
        "feature_filter_settings_json": json.dumps(row.feature_filter_settings, sort_keys=True),
        "feature_filter_skip_counts_json": json.dumps(row.feature_filter_skip_counts, sort_keys=True),
        "risk_control_settings_json": json.dumps(row.risk_control_settings, sort_keys=True),
        "risk_control_skip_counts_json": json.dumps(row.risk_control_skip_counts, sort_keys=True),
        "regime_filter_settings_json": json.dumps(row.regime_filter_settings, sort_keys=True),
        "regime_filter_skip_counts_json": json.dumps(row.regime_filter_skip_counts, sort_keys=True),
        "confirmation_filter_settings_json": json.dumps(row.confirmation_filter_settings, sort_keys=True),
        "confirmation_filter_skip_counts_json": json.dumps(row.confirmation_filter_skip_counts, sort_keys=True),
        "exit_profile_settings_json": json.dumps(row.exit_profile_settings, sort_keys=True),
        "exit_profile_counts_json": json.dumps(row.exit_profile_counts, sort_keys=True),
        "cost_model_settings_json": json.dumps(row.cost_model_settings, sort_keys=True),
        "feature_artifact_paths_json": json.dumps(row.feature_artifact_paths, sort_keys=True),
        "downloaded_csv_paths_json": json.dumps(row.downloaded_csv_paths, sort_keys=True),
        "manifest_path": row.manifest_path,
        "artifact_dir": row.artifact_dir,
    }


def _feature_artifact_paths(paths: list[str]) -> dict[str, str]:
    suffixes = {
        "entry_feature_snapshots": "-entry-feature-snapshots.csv",
        "feature_bucket_pnl": "-feature-bucket-pnl.csv",
        "regime_bucket_summary": "-regime-bucket-summary.csv",
        "worst_day_attribution": "-worst-day-attribution.csv",
        "forward_path_diagnostics": "-forward-path-diagnostics.csv",
        "holding_horizon_pnl": "-holding-horizon-pnl.csv",
        "path_risk_diagnostics": "-path-risk-diagnostics.csv",
        "path_risk_threshold_summary": "-path-risk-threshold-summary.csv",
    }
    return {
        key: path
        for key, suffix in suffixes.items()
        for path in paths
        if path.endswith(suffix)
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


def _cached_public_download(
    *,
    start: datetime,
    end: datetime,
    market_data_dir: str | Path,
    symbol: str,
) -> PublicDownloadResult:
    csv_paths = {
        timeframe: str(
            Path(market_data_dir)
            / "bybit"
            / "linear"
            / symbol
            / timeframe
            / f"{_cache_timestamp(start)}_{_cache_timestamp(end)}.csv"
        )
        for timeframe in ("M15", "H1", "H4", "D1")
    }
    missing = [path for path in csv_paths.values() if not Path(path).exists()]
    if missing:
        msg = "cached public market-data CSVs are missing: " + ", ".join(missing)
        raise FileNotFoundError(msg)
    return PublicDownloadResult(
        symbol=symbol,
        requested_start=start,
        requested_end=end,
        csv_paths=csv_paths,
        source_metadata={
            "source": "bybit_public",
            "provider": "bybit",
            "cache_mode": "reuse_market_data",
            "csv_paths": csv_paths,
        },
    )


def _cache_timestamp(value: datetime) -> str:
    return to_utc(value).strftime("%Y%m%dT%H%M%SZ")


def _batch_id(
    *,
    windows: list[BatchWindow],
    thresholds: ResearchThresholds,
    gate_profile: str,
    gate_settings: dict[str, Any],
    feature_filter_profile: str = "none",
    feature_filter_settings: dict[str, Any] | None = None,
    risk_control_profile: str = "none",
    risk_control_settings: dict[str, Any] | None = None,
    regime_filter_profile: str = "none",
    regime_filter_settings: dict[str, Any] | None = None,
    confirmation_filter_profile: str = "none",
    confirmation_filter_settings: dict[str, Any] | None = None,
    exit_profile: str = "none",
    exit_profile_settings: dict[str, Any] | None = None,
    cost_model_settings: dict[str, Any] | None = None,
    bad_regime_diagnostics_enabled: bool = False,
    forward_path_diagnostics_enabled: bool = False,
    path_risk_diagnostics_enabled: bool = False,
) -> str:
    payload = {
        "windows": [
            {"label": window.label, "start": _format_datetime(window.start), "end": _format_datetime(window.end)}
            for window in windows
        ],
        "thresholds": thresholds.model_dump(mode="json"),
        "gate_profile": gate_profile,
        "gate_settings": gate_settings,
        "feature_filter_profile": feature_filter_profile,
        "feature_filter_settings": feature_filter_settings or {},
        "risk_control_profile": risk_control_profile,
        "risk_control_settings": risk_control_settings or {},
        "regime_filter_profile": regime_filter_profile,
        "regime_filter_settings": regime_filter_settings or {},
        "confirmation_filter_profile": confirmation_filter_profile,
        "confirmation_filter_settings": confirmation_filter_settings or {},
        "exit_profile": exit_profile,
        "exit_profile_settings": exit_profile_settings or {},
        "cost_model_settings": cost_model_settings or {},
        "bad_regime_diagnostics_enabled": bad_regime_diagnostics_enabled,
        "forward_path_diagnostics_enabled": forward_path_diagnostics_enabled,
        "path_risk_diagnostics_enabled": path_risk_diagnostics_enabled,
        "symbol": "BTCUSDT",
        "source": "bybit_public",
        "execution_timeframe": "M15",
    }
    return stable_hash(payload).split(":", maxsplit=1)[1][:16]


def _cost_model_settings(
    *,
    spread: float,
    slippage: float,
    commission_per_unit: float,
    funding_per_bar: float,
    commission_rate: float,
    funding_rate_per_bar: float,
) -> dict[str, float]:
    return {
        "spread": spread,
        "slippage_per_unit": slippage,
        "commission_per_unit": commission_per_unit,
        "funding_per_bar": funding_per_bar,
        "commission_rate": commission_rate,
        "funding_rate_per_bar": funding_rate_per_bar,
    }


def _format_datetime(value: datetime) -> str:
    return to_utc(value).isoformat().replace("+00:00", "Z")


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str) and value.strip():
        try:
            return float(value)
        except ValueError:
            return None
    return None


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
    parser.add_argument(
        "--gate-profile",
        choices=[
            "baseline",
            "conservative-v1",
            "conservative-v1-m15-slope-positive",
            "conservative-v1-h1-long",
            "conservative-v1-m15-slope-positive-h1-long",
            "conservative-v1-m15-slope-positive-body-cap",
            "conservative-v1-m15-slope-positive-daily-stop-3000",
            "conservative-v1-m15-slope-positive-daily-stop-2000",
            "conservative-v1-m15-slope-positive-max-trades-8",
            "conservative-v1-m15-slope-positive-max-trades-8-atr25-block",
            "conservative-v1-m15-slope-positive-max-trades-8-atr25-breakout1-block",
            "conservative-v1-m15-slope-positive-max-trades-8-atr25-body75-block",
            "conservative-v1-m15-slope-positive-max-trades-8-atr25-body25-75-block",
            "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1",
            "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-2",
            "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-closepos70",
            "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-no-return-inside-range",
            "conservative-v1-m15-slope-positive-loss-cooldown-12",
            *sorted(EXIT_PROFILE_NAMES),
        ],
        default="baseline",
    )
    parser.add_argument("--min-trade-count", type=int, default=1)
    parser.add_argument("--min-net-profit", type=float, default=0.0)
    parser.add_argument("--min-profit-factor", type=float, default=1.0)
    parser.add_argument("--min-max-drawdown", type=float, default=-0.35)
    parser.add_argument("--spread", type=float, default=0.10)
    parser.add_argument("--slippage", type=float, default=0.02)
    parser.add_argument("--commission-per-unit", type=float, default=0.01)
    parser.add_argument("--funding-per-bar", type=float, default=0.0)
    parser.add_argument("--commission-rate", type=float, default=0.0)
    parser.add_argument("--funding-rate-per-bar", type=float, default=0.0)
    parser.add_argument("--bad-regime-diagnostics", action="store_true")
    parser.add_argument("--forward-path-diagnostics", action="store_true")
    parser.add_argument("--path-risk-diagnostics", action="store_true")
    parser.add_argument(
        "--reuse-market-data",
        action="store_true",
        help="Reuse cached Bybit CSV files from --market-data-dir instead of downloading.",
    )
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
        gate_profile=args.gate_profile,
        enable_bad_regime_diagnostics=args.bad_regime_diagnostics,
        enable_forward_path_diagnostics=args.forward_path_diagnostics,
        enable_path_risk_diagnostics=args.path_risk_diagnostics,
        reuse_market_data=args.reuse_market_data,
        spread=args.spread,
        slippage=args.slippage,
        commission_per_unit=args.commission_per_unit,
        funding_per_bar=args.funding_per_bar,
        commission_rate=args.commission_rate,
        funding_rate_per_bar=args.funding_rate_per_bar,
        symbol=args.symbol,
        continue_on_error=not args.stop_on_error,
    )
    print(json.dumps(result.summary.model_dump(mode="json"), sort_keys=True, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
