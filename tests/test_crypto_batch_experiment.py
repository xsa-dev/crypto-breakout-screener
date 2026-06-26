import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from src.app.breakout.experiments.crypto_backtest import (
    CryptoExperimentResult,
    PublicDownloadResult,
)
from src.app.breakout.experiments.crypto_batch import (
    BatchWindow,
    ResearchThresholds,
    exit_profile_config,
    parse_windows,
    run_batch_experiment,
)


def test_batch_runner_writes_deterministic_summary_and_research_verdict(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BYBIT_API_KEY", "SHOULD_NOT_APPEAR")
    windows = [
        BatchWindow(
            label="w1",
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 2, tzinfo=UTC),
        ),
        BatchWindow(
            label="w2",
            start=datetime(2024, 1, 2, tzinfo=UTC),
            end=datetime(2024, 1, 3, tzinfo=UTC),
        ),
    ]
    download = _fake_download_factory(tmp_path)
    run_single = _fake_run_factory(tmp_path)

    first = run_batch_experiment(
        windows=windows,
        output_dir=tmp_path / "backtests",
        market_data_dir=tmp_path / "market-data",
        download=download,
        run_single=run_single,
    )
    second = run_batch_experiment(
        windows=windows,
        output_dir=tmp_path / "backtests",
        market_data_dir=tmp_path / "market-data",
        download=download,
        run_single=run_single,
    )

    assert first.batch_id == second.batch_id
    assert first.summary.aggregate.technical_pass is True
    assert first.summary.aggregate.hypothesis_supported is True
    assert first.summary.aggregate.hypothesis_not_supported is False
    assert first.summary.aggregate.total_trade_count == 20
    assert first.summary.aggregate.total_net_profit == 200.0
    assert first.summary.summary_csv_path == str(first.summary_csv_path)
    assert first.summary.summary_json_path == str(first.summary_json_path)
    assert first.summary_csv_path.read_text(encoding="utf-8") == second.summary_csv_path.read_text(
        encoding="utf-8"
    )
    summary_text = first.summary_json_path.read_text(encoding="utf-8")
    assert "SHOULD_NOT_APPEAR" not in summary_text
    summary = json.loads(summary_text)
    assert summary["aggregate"]["research_notice"].startswith("research-only")
    assert [row["window_label"] for row in summary["windows"]] == ["w1", "w2"]
    assert set(summary["windows"][0]["context_timeframes_available"]) == {"H1", "H4", "D1"}

    with first.summary_csv_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["status"] == "passed"
    assert rows[0]["profit_factor"] == "1.5"
    assert set(json.loads(rows[0]["downloaded_csv_paths_json"])) == {"M15", "H1", "H4", "D1"}
    assert rows[0]["gate_profile"] == "baseline"
    assert "min_entry_score" in json.loads(rows[0]["gate_settings_json"])
    assert "entry_feature_snapshots" in json.loads(rows[0]["feature_artifact_paths_json"])


def test_batch_runner_records_conservative_gate_profile(tmp_path) -> None:
    windows = [
        BatchWindow(
            label="gated",
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 2, tzinfo=UTC),
        )
    ]
    seen_gates: list[dict[str, Any]] = []

    def run_single(**kwargs: Any) -> CryptoExperimentResult:
        seen_gates.append(kwargs["research_gates"].model_dump(mode="json"))
        return _fake_run_factory(tmp_path)(**kwargs)

    result = run_batch_experiment(
        windows=windows,
        output_dir=tmp_path / "backtests",
        market_data_dir=tmp_path / "market-data",
        gate_profile="conservative-v1",
        download=_fake_download_factory(tmp_path),
        run_single=run_single,
    )

    row = result.summary.windows[0]
    assert result.summary.gate_profile == "conservative-v1"
    assert row.gate_profile == "conservative-v1"
    assert row.gate_settings["block_immediate_reentry"] is True
    assert seen_gates[0]["cooldown_bars_after_loss"] == 6



def test_batch_runner_records_feature_filter_profile(tmp_path) -> None:
    windows = [
        BatchWindow(
            label="filtered",
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 2, tzinfo=UTC),
        )
    ]
    seen_filters: list[dict[str, Any]] = []

    def run_single(**kwargs: Any) -> CryptoExperimentResult:
        seen_filters.append(kwargs["feature_filters"].model_dump(mode="json"))
        return _fake_run_factory(tmp_path)(**kwargs)

    result = run_batch_experiment(
        windows=windows,
        output_dir=tmp_path / "backtests",
        market_data_dir=tmp_path / "market-data",
        gate_profile="conservative-v1-m15-slope-positive",
        download=_fake_download_factory(tmp_path),
        run_single=run_single,
    )

    row = result.summary.windows[0]
    assert result.summary.gate_profile == "conservative-v1-m15-slope-positive"
    assert result.summary.feature_filter_profile == "conservative-v1-m15-slope-positive"
    assert row.feature_filter_profile == "conservative-v1-m15-slope-positive"
    assert row.gate_settings["block_immediate_reentry"] is True
    assert row.feature_filter_settings["require_m15_ema_slope_positive"] is True
    assert row.feature_filter_skip_counts == {"skipped_feature_m15_ema_slope_not_positive": 3}
    assert seen_filters[0]["require_m15_ema_slope_positive"] is True

    with result.summary_csv_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["feature_filter_profile"] == "conservative-v1-m15-slope-positive"
    assert json.loads(rows[0]["feature_filter_settings_json"])["require_m15_ema_slope_positive"] is True
    assert json.loads(rows[0]["feature_filter_skip_counts_json"]) == {"skipped_feature_m15_ema_slope_not_positive": 3}



def test_batch_runner_records_drawdown_risk_control_profile(tmp_path) -> None:
    windows = [
        BatchWindow(
            label="risk",
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 2, tzinfo=UTC),
        )
    ]
    seen_gates: list[dict[str, Any]] = []
    seen_filters: list[dict[str, Any]] = []

    def run_single(**kwargs: Any) -> CryptoExperimentResult:
        seen_gates.append(kwargs["research_gates"].model_dump(mode="json"))
        seen_filters.append(kwargs["feature_filters"].model_dump(mode="json"))
        return _fake_run_factory(tmp_path)(**kwargs)

    result = run_batch_experiment(
        windows=windows,
        output_dir=tmp_path / "backtests",
        market_data_dir=tmp_path / "market-data",
        gate_profile="conservative-v1-m15-slope-positive-daily-stop-3000",
        download=_fake_download_factory(tmp_path),
        run_single=run_single,
    )

    row = result.summary.windows[0]
    assert result.summary.feature_filter_profile == "conservative-v1-m15-slope-positive"
    assert result.summary.risk_control_profile == "conservative-v1-m15-slope-positive-daily-stop-3000"
    assert row.risk_control_profile == "conservative-v1-m15-slope-positive-daily-stop-3000"
    assert row.risk_control_settings["daily_stop_loss"] == 3000.0
    assert row.risk_control_skip_counts == {
        "skipped_cooldown": 5,
        "skipped_daily_stop_loss": 2,
        "skipped_max_trades_per_day": 4,
    }
    assert seen_gates[0]["daily_stop_loss"] == 3000.0
    assert seen_filters[0]["require_m15_ema_slope_positive"] is True

    with result.summary_csv_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["risk_control_profile"] == "conservative-v1-m15-slope-positive-daily-stop-3000"
    assert json.loads(rows[0]["risk_control_settings_json"])["daily_stop_loss"] == 3000.0
    assert json.loads(rows[0]["risk_control_skip_counts_json"]) == row.risk_control_skip_counts




def test_batch_runner_records_volatility_regime_filter_profile(tmp_path) -> None:
    windows = [
        BatchWindow(
            label="regime",
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 2, tzinfo=UTC),
        )
    ]
    seen_gates: list[dict[str, Any]] = []
    seen_filters: list[dict[str, Any]] = []

    def run_single(**kwargs: Any) -> CryptoExperimentResult:
        seen_gates.append(kwargs["research_gates"].model_dump(mode="json"))
        seen_filters.append(kwargs["feature_filters"].model_dump(mode="json"))
        return _fake_run_factory(tmp_path)(**kwargs)

    profile = "conservative-v1-m15-slope-positive-max-trades-8-atr25-breakout1-block"
    result = run_batch_experiment(
        windows=windows,
        output_dir=tmp_path / "backtests",
        market_data_dir=tmp_path / "market-data",
        gate_profile=profile,
        download=_fake_download_factory(tmp_path),
        run_single=run_single,
    )

    row = result.summary.windows[0]
    assert result.summary.gate_profile == profile
    assert result.summary.feature_filter_profile == "conservative-v1-m15-slope-positive"
    assert result.summary.risk_control_profile == "conservative-v1-m15-slope-positive-max-trades-8"
    assert result.summary.regime_filter_profile == profile
    assert row.regime_filter_profile == profile
    assert row.regime_filter_settings == {
        "max_breakout_distance_atr": 1.0,
        "min_atr_percentile": 0.25,
    }
    assert row.regime_filter_skip_counts == {
        "skipped_feature_atr_percentile_below_min": 7,
        "skipped_feature_breakout_distance_atr_above_cap": 11,
        "skipped_feature_candle_body_ratio_above_cap": 13,
    }
    assert seen_gates[0]["max_trades_per_day"] == 8
    assert seen_filters[0]["require_m15_ema_slope_positive"] is True
    assert seen_filters[0]["min_atr_percentile"] == 0.25
    assert seen_filters[0]["max_breakout_distance_atr"] == 1.0

    with result.summary_csv_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["regime_filter_profile"] == profile
    assert json.loads(rows[0]["regime_filter_settings_json"]) == row.regime_filter_settings
    assert json.loads(rows[0]["regime_filter_skip_counts_json"]) == row.regime_filter_skip_counts

    summary = json.loads(result.summary_json_path.read_text(encoding="utf-8"))
    assert summary["regime_filter_profile"] == profile
    assert summary["regime_filter_settings"] == row.regime_filter_settings



def test_batch_runner_records_confirmation_filter_profile(tmp_path) -> None:
    windows = [
        BatchWindow(
            label="confirm",
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 2, tzinfo=UTC),
        )
    ]
    seen_gates: list[dict[str, Any]] = []
    seen_filters: list[dict[str, Any]] = []
    seen_confirmation: list[dict[str, Any]] = []

    def run_single(**kwargs: Any) -> CryptoExperimentResult:
        seen_gates.append(kwargs["research_gates"].model_dump(mode="json"))
        seen_filters.append(kwargs["feature_filters"].model_dump(mode="json"))
        seen_confirmation.append(kwargs["confirmation_filters"].model_dump(mode="json"))
        return _fake_run_factory(tmp_path)(**kwargs)

    profile = "conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-closepos70"
    result = run_batch_experiment(
        windows=windows,
        output_dir=tmp_path / "backtests",
        market_data_dir=tmp_path / "market-data",
        gate_profile=profile,
        download=_fake_download_factory(tmp_path),
        run_single=run_single,
    )

    row = result.summary.windows[0]
    assert result.summary.gate_profile == profile
    assert result.summary.feature_filter_profile == "conservative-v1-m15-slope-positive"
    assert result.summary.risk_control_profile == "conservative-v1-m15-slope-positive-max-trades-8"
    assert result.summary.confirmation_filter_profile == profile
    assert row.confirmation_filter_profile == profile
    assert row.confirmation_filter_settings == {
        "cancel_on_return_inside_range": False,
        "min_close_position": 0.7,
        "required_closes_above_breakout": 1,
    }
    assert row.confirmation_filter_skip_counts == {
        "skipped_confirmation_close_not_above_breakout": 17,
        "skipped_confirmation_close_position_below_min": 19,
        "skipped_confirmation_returned_inside_range": 23,
    }
    assert seen_gates[0]["max_trades_per_day"] == 8
    assert seen_filters[0]["require_m15_ema_slope_positive"] is True
    assert seen_confirmation[0]["required_closes_above_breakout"] == 1
    assert seen_confirmation[0]["min_close_position"] == 0.7

    with result.summary_csv_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["confirmation_filter_profile"] == profile
    assert json.loads(rows[0]["confirmation_filter_settings_json"]) == row.confirmation_filter_settings
    assert json.loads(rows[0]["confirmation_filter_skip_counts_json"]) == row.confirmation_filter_skip_counts

    summary = json.loads(result.summary_json_path.read_text(encoding="utf-8"))
    assert summary["confirmation_filter_profile"] == profile
    assert summary["confirmation_filter_settings"] == row.confirmation_filter_settings



def test_batch_runner_records_exit_profile(tmp_path) -> None:
    windows = [
        BatchWindow(
            label="exit",
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 2, tzinfo=UTC),
        )
    ]
    seen_exit_profiles: list[dict[str, Any]] = []

    def run_single(**kwargs: Any) -> CryptoExperimentResult:
        seen_exit_profiles.append(kwargs["exit_profile"].model_dump(mode="json"))
        return _fake_run_factory(tmp_path)(**kwargs)

    profile = "conservative-v1-m15-slope-positive-max-trades-8-atr-stop-1p0-target-1p5"
    result = run_batch_experiment(
        windows=windows,
        output_dir=tmp_path / "backtests",
        market_data_dir=tmp_path / "market-data",
        gate_profile=profile,
        download=_fake_download_factory(tmp_path),
        run_single=run_single,
    )

    row = result.summary.windows[0]
    assert result.summary.exit_profile == profile
    assert row.exit_profile == profile
    assert row.exit_profile_settings == {
        "fixed_holding_bars": 4,
        "stop_atr": 1.0,
        "target_atr": 1.5,
    }
    assert seen_exit_profiles == [row.exit_profile_settings]
    assert exit_profile_config(profile).model_dump(mode="json") == row.exit_profile_settings

    with result.summary_csv_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["exit_profile"] == profile
    assert json.loads(rows[0]["exit_profile_settings_json"]) == row.exit_profile_settings
    assert json.loads(rows[0]["exit_profile_counts_json"]) == row.exit_profile_counts

    summary = json.loads(result.summary_json_path.read_text(encoding="utf-8"))
    assert summary["exit_profile"] == profile
    assert summary["exit_profile_settings"] == row.exit_profile_settings

    tight_stop_profile = "conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p01-target-2p0"
    assert exit_profile_config(tight_stop_profile).model_dump(mode="json") == {
        "fixed_holding_bars": 1,
        "stop_atr": 0.01,
        "target_atr": 2.0,
    }



def test_batch_runner_writes_bad_regime_diagnostics_for_failed_windows(tmp_path) -> None:
    windows = [
        BatchWindow(
            label="pass",
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 2, tzinfo=UTC),
        ),
        BatchWindow(
            label="fail",
            start=datetime(2024, 1, 2, tzinfo=UTC),
            end=datetime(2024, 1, 3, tzinfo=UTC),
        ),
    ]

    def run_single(**kwargs: Any) -> CryptoExperimentResult:
        csv_path = Path(kwargs["csv_path"])
        net = -50.0 if csv_path.stem == "20240102" else 100.0
        pf = 0.8 if csv_path.stem == "20240102" else 1.5
        return _fake_run_factory(tmp_path, net_profit=net, profit_factor=pf)(**kwargs)

    result = run_batch_experiment(
        windows=windows,
        output_dir=tmp_path / "backtests",
        market_data_dir=tmp_path / "market-data",
        gate_profile="conservative-v1-m15-slope-positive-max-trades-8",
        enable_bad_regime_diagnostics=True,
        download=_fake_download_factory(tmp_path),
        run_single=run_single,
    )

    assert result.summary.bad_regime_diagnostics_enabled is True
    paths = {key: Path(value) for key, value in result.summary.diagnostic_artifact_paths.items()}
    assert set(paths) == {
        "bad_regime_bucket_summary",
        "failed_window_diagnostics",
        "worst_drawdown_runs",
    }

    with paths["failed_window_diagnostics"].open(newline="", encoding="utf-8") as file:
        failed_rows = list(csv.DictReader(file))
    assert [row["window_label"] for row in failed_rows] == ["fail"]
    assert failed_rows[0]["profile"] == "conservative-v1-m15-slope-positive-max-trades-8"
    assert failed_rows[0]["failure_class"] == "negative_or_flat_expectancy"

    with paths["worst_drawdown_runs"].open(newline="", encoding="utf-8") as file:
        drawdown_rows = list(csv.DictReader(file))
    assert drawdown_rows[0]["window_label"] == "fail"
    assert drawdown_rows[0]["min_drawdown"] == "-0.42"
    assert drawdown_rows[0]["worst_negative_day"] == "2024-01-02"

    with paths["bad_regime_bucket_summary"].open(newline="", encoding="utf-8") as file:
        bucket_rows = list(csv.DictReader(file))
    assert {row["window_label"] for row in bucket_rows} == {"fail"}
    assert {row["bucket_source"] for row in bucket_rows} == {"feature_bucket_pnl", "regime_bucket_summary"}
    assert {row["no_lookahead_source"] for row in bucket_rows} == {"entry_feature_snapshot"}

    summary = json.loads(result.summary_json_path.read_text(encoding="utf-8"))
    assert summary["bad_regime_diagnostics_enabled"] is True
    assert set(summary["diagnostic_artifact_paths"]) == set(paths)


def test_batch_verdict_blocks_failed_thresholds(tmp_path) -> None:
    windows = [
        BatchWindow(
            label="loss",
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 2, tzinfo=UTC),
        )
    ]

    result = run_batch_experiment(
        windows=windows,
        output_dir=tmp_path / "backtests",
        market_data_dir=tmp_path / "market-data",
        thresholds=ResearchThresholds(min_net_profit=0.0, min_profit_factor=1.0),
        download=_fake_download_factory(tmp_path),
        run_single=_fake_run_factory(tmp_path, net_profit=-10.0, profit_factor=0.9),
    )

    row = result.summary.windows[0]
    assert row.status == "blocked"
    assert "net_profit_below_threshold" in row.blockers
    assert "profit_factor_below_threshold" in row.blockers
    assert result.summary.aggregate.technical_pass is True
    assert result.summary.aggregate.hypothesis_supported is False
    assert result.summary.aggregate.hypothesis_not_supported is True
    assert any("loss:net_profit_below_threshold" in blocker for blocker in result.summary.aggregate.blockers)


def test_batch_runner_records_failed_window_without_passing_batch(tmp_path) -> None:
    windows = [
        BatchWindow(
            label="ok",
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 2, tzinfo=UTC),
        ),
        BatchWindow(
            label="bad",
            start=datetime(2024, 1, 2, tzinfo=UTC),
            end=datetime(2024, 1, 3, tzinfo=UTC),
        ),
    ]

    def download(**kwargs: Any) -> PublicDownloadResult:
        start = kwargs["start"]
        if start.day == 2:
            msg = "provider unavailable"
            raise RuntimeError(msg)
        return _fake_download_factory(tmp_path)(**kwargs)

    result = run_batch_experiment(
        windows=windows,
        output_dir=tmp_path / "backtests",
        market_data_dir=tmp_path / "market-data",
        download=download,
        run_single=_fake_run_factory(tmp_path),
    )

    assert [row.status for row in result.summary.windows] == ["passed", "failed"]
    assert result.summary.windows[1].blockers[0].startswith("window_exception:RuntimeError")
    assert result.summary.aggregate.technical_pass is False
    assert result.summary.aggregate.hypothesis_supported is False


def test_batch_input_validation_and_window_parsing(tmp_path) -> None:
    windows = parse_windows("one:2024-01-01T00:00:00Z/2024-01-02T00:00:00Z")
    assert windows[0].label == "one"
    assert windows[0].start == datetime(2024, 1, 1, tzinfo=UTC)

    with pytest.raises(ValueError, match="BTCUSDT only"):
        run_batch_experiment(
            windows=windows,
            symbol="ETHUSDT",
            output_dir=tmp_path,
            market_data_dir=tmp_path,
            download=_fake_download_factory(tmp_path),
            run_single=_fake_run_factory(tmp_path),
        )
    with pytest.raises(ValueError, match="at least one"):
        run_batch_experiment(
            windows=[],
            output_dir=tmp_path,
            market_data_dir=tmp_path,
            download=_fake_download_factory(tmp_path),
            run_single=_fake_run_factory(tmp_path),
        )


def _fake_download_factory(tmp_path: Path):
    def download(**kwargs: Any) -> PublicDownloadResult:
        start = kwargs["start"]
        end = kwargs["end"]
        label = start.strftime("%Y%m%d")
        paths = {
            timeframe: str(tmp_path / "market-data" / timeframe / f"{label}.csv")
            for timeframe in ("M15", "H1", "H4", "D1")
        }
        for path in paths.values():
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text("timestamp,open,high,low,close,volume,source\n", encoding="utf-8")
        return PublicDownloadResult(
            symbol="BTCUSDT",
            requested_start=start,
            requested_end=end,
            csv_paths=paths,
            source_metadata={
                "source": "bybit_public",
                "provider": "bybit",
                "csv_paths": paths,
                "timeframe_metadata": {
                    timeframe: {"accepted_row_count": 1, "page_count": 1} for timeframe in paths
                },
            },
        )

    return download


def _fake_run_factory(
    tmp_path: Path,
    *,
    net_profit: float = 100.0,
    profit_factor: float = 1.5,
    feed_gaps: list[dict[str, Any]] | None = None,
):
    def run_single(**kwargs: Any) -> CryptoExperimentResult:
        csv_path = Path(kwargs["csv_path"])
        label = csv_path.stem
        run_id = f"run-{label}"
        output_dir = Path(kwargs["output_dir"])
        artifact_dir = output_dir / "crypto" / "BTCUSDT" / run_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        metrics_path = artifact_dir / f"{run_id}-metrics.csv"
        entry_features_path = artifact_dir / f"{run_id}-entry-feature-snapshots.csv"
        feature_bucket_path = artifact_dir / f"{run_id}-feature-bucket-pnl.csv"
        regime_bucket_path = artifact_dir / f"{run_id}-regime-bucket-summary.csv"
        worst_day_path = artifact_dir / f"{run_id}-worst-day-attribution.csv"
        drawdown_path = artifact_dir / f"{run_id}-drawdown.csv"
        forward_path = artifact_dir / f"{run_id}-forward-path-diagnostics.csv"
        holding_path = artifact_dir / f"{run_id}-holding-horizon-pnl.csv"
        path_risk_path = artifact_dir / f"{run_id}-path-risk-diagnostics.csv"
        path_risk_summary_path = artifact_dir / f"{run_id}-path-risk-threshold-summary.csv"
        parameters_path = artifact_dir / f"{run_id}-parameters.json"
        metrics_path.write_text(
            "metric,value\n"
            "trade_count,10\n"
            f"net_profit,{net_profit}\n"
            "max_drawdown,-0.1\n"
            f"profit_factor,{profit_factor}\n"
            "win_rate,0.6\n"
            "sharpe_ratio,0.4\n"
            "average_trade,10\n"
            "expectancy,10\n",
            encoding="utf-8",
        )
        manifest_path = artifact_dir / f"{run_id}-dataset-manifest.json"
        entry_features_path.write_text("placeholder\n", encoding="utf-8")
        feature_bucket_path.write_text(
            "feature,bucket,trade_count,net_pnl,average_trade,win_rate,profit_factor\n"
            "atr_percentile,0.75..1.0,4,-120.0,-30.0,0.25,0.5\n"
            "candle_body_ratio,0.5..0.75,6,220.0,36.6666666667,0.66,2.0\n",
            encoding="utf-8",
        )
        regime_bucket_path.write_text(
            "regime,trade_count,net_pnl,average_trade,win_rate,profit_factor\n"
            "atr=0.75..1.0|body=0.5..0.75|h1=long,4,-120.0,-30.0,0.25,0.5\n",
            encoding="utf-8",
        )
        worst_day_path.write_text(
            "day,trade_count,net_pnl,dominant_atr_bucket,dominant_candle_body_bucket,context_available\n"
            "2024-01-02,3,-150.0,0.75..1.0,0.5..0.75,True\n",
            encoding="utf-8",
        )
        drawdown_path.write_text(
            "timestamp,drawdown\n"
            "2024-01-01T00:00:00+00:00,0\n"
            "2024-01-02T00:00:00+00:00,-0.42\n",
            encoding="utf-8",
        )
        artifact_paths = [
            str(metrics_path),
            str(entry_features_path),
            str(feature_bucket_path),
            str(regime_bucket_path),
            str(worst_day_path),
            str(drawdown_path),
            str(parameters_path),
            str(manifest_path),
        ]
        if kwargs.get("forward_path_diagnostics"):
            forward_path.write_text(
                "trade_id,horizon_bars,available,forward_return,mfe,mae,close_above_entry,returned_to_breakout_level,crossed_below_entry\n"
                f"{run_id}-1,1,True,0.02,3.0,-1.0,True,False,False\n"
                f"{run_id}-2,1,True,-0.01,1.0,-2.0,False,True,True\n",
                encoding="utf-8",
            )
            holding_path.write_text(
                "horizon_bars,trade_count,available_count,unavailable_count,synthetic_net_pnl,average_forward_return,average_mfe,average_mae,positive_forward_return_ratio\n"
                "1,2,2,0,42.0,0.005,2.0,-1.5,0.5\n",
                encoding="utf-8",
            )
            artifact_paths.extend([str(forward_path), str(holding_path)])
        if kwargs.get("path_risk_diagnostics"):
            path_risk_path.write_text(
                "trade_id,horizon_bars,available,max_favorable_atr,max_adverse_atr,breakeven_reachable,breakeven_touched_after_reach,fav_1p0_before_adv_1p0,adv_1p0_before_fav_1p0,trail_after_fav_1p0_giveback_0p5_touched,trail_after_fav_1p0_giveback_1p0_touched\n"
                f"{run_id}-1,1,True,1.5,0.8,True,False,True,False,True,False\n"
                f"{run_id}-2,1,True,0.7,1.2,False,unavailable,False,True,unavailable,unavailable\n",
                encoding="utf-8",
            )
            path_risk_summary_path.write_text(
                "horizon_bars,trade_count,available_count,unavailable_count,average_max_favorable_atr,median_max_favorable_atr,average_max_adverse_atr,median_max_adverse_atr,breakeven_reachable_ratio,breakeven_touched_after_reach_ratio\n"
                "1,2,2,0,1.1,1.1,1.0,1.0,0.5,0.0\n",
                encoding="utf-8",
            )
            artifact_paths.extend([str(path_risk_path), str(path_risk_summary_path)])
        manifest_path.write_text(
            json.dumps(
                {
                    "feed_gaps": feed_gaps or [],
                    "available_context_timeframes": ["H1", "H4", "D1"],
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        parameters_path.write_text(
            json.dumps(
                {
                    "feature_filters": kwargs["feature_filters"].model_dump(mode="json"),
                    "confirmation_filters": kwargs["confirmation_filters"].model_dump(mode="json"),
                    "exit_profile": kwargs["exit_profile"].model_dump(mode="json"),
                    "exit_profile_counts": {"fixed_holding_close": 10},
                    "research_gate_skip_counts": {
                        "skipped_confirmation_close_not_above_breakout": 17,
                        "skipped_confirmation_close_position_below_min": 19,
                        "skipped_confirmation_returned_inside_range": 23,
                        "skipped_feature_m15_ema_slope_not_positive": 3,
                        "skipped_feature_atr_percentile_below_min": 7,
                        "skipped_feature_breakout_distance_atr_above_cap": 11,
                        "skipped_feature_candle_body_ratio_above_cap": 13,
                        "skipped_cooldown": 5,
                        "skipped_daily_stop_loss": 2,
                        "skipped_max_trades_per_day": 4,
                    },
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return CryptoExperimentResult(
            run_id=run_id,
            symbol="BTCUSDT",
            timeframe="M15",
            bar_count=100,
            dataset_hash=f"sha256:dataset-{label}",
            config_hash="sha256:config",
            trade_count=10,
            net_pnl=net_profit,
            max_drawdown=-0.1,
            win_rate=0.6,
            artifact_dir=artifact_dir,
            manifest_path=manifest_path,
            artifact_paths=artifact_paths,
        )

    return run_single


def test_batch_runner_writes_forward_path_diagnostic_summaries(tmp_path) -> None:
    windows = [
        BatchWindow(
            label="forward-pass",
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 2, tzinfo=UTC),
        ),
        BatchWindow(
            label="forward-fail",
            start=datetime(2024, 1, 2, tzinfo=UTC),
            end=datetime(2024, 1, 3, tzinfo=UTC),
        ),
    ]

    result = run_batch_experiment(
        windows=windows,
        output_dir=tmp_path / "backtests",
        market_data_dir=tmp_path / "market-data",
        gate_profile="conservative-v1-m15-slope-positive-max-trades-8",
        enable_forward_path_diagnostics=True,
        download=_fake_download_factory(tmp_path),
        run_single=_fake_run_factory(tmp_path, net_profit=100.0, profit_factor=1.5),
    )

    assert result.summary.forward_path_diagnostics_enabled is True
    paths = result.summary.diagnostic_artifact_paths
    assert set(paths) == {"forward_path_window_summary", "passed_vs_failed_forward_path_summary"}
    assert Path(paths["forward_path_window_summary"]).exists()
    assert Path(paths["passed_vs_failed_forward_path_summary"]).exists()
    assert all("forward_path_diagnostics" in row.feature_artifact_paths for row in result.summary.windows)
    assert all("holding_horizon_pnl" in row.feature_artifact_paths for row in result.summary.windows)

    with Path(paths["forward_path_window_summary"]).open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 2
    assert rows[0]["horizon_bars"] == "1"
    assert rows[0]["synthetic_net_pnl"] == "42.0"

    with Path(paths["passed_vs_failed_forward_path_summary"]).open(newline="", encoding="utf-8") as file:
        grouped = list(csv.DictReader(file))
    assert grouped
    assert grouped[0]["window_group"] == "passed"
    assert grouped[0]["positive_forward_return_ratio"] == "0.5"

    summary = json.loads(result.summary_json_path.read_text(encoding="utf-8"))
    assert summary["forward_path_diagnostics_enabled"] is True
    assert summary["diagnostic_artifact_paths"] == paths


def test_batch_runner_writes_path_risk_diagnostic_summaries(tmp_path) -> None:
    windows = [
        BatchWindow(
            label="path-pass",
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 2, tzinfo=UTC),
        ),
        BatchWindow(
            label="path-fail",
            start=datetime(2024, 1, 2, tzinfo=UTC),
            end=datetime(2024, 1, 3, tzinfo=UTC),
        ),
    ]

    result = run_batch_experiment(
        windows=windows,
        output_dir=tmp_path / "backtests",
        market_data_dir=tmp_path / "market-data",
        gate_profile="conservative-v1-m15-slope-positive-max-trades-8",
        enable_path_risk_diagnostics=True,
        download=_fake_download_factory(tmp_path),
        run_single=_fake_run_factory(tmp_path, net_profit=100.0, profit_factor=1.5),
    )

    assert result.summary.path_risk_diagnostics_enabled is True
    paths = result.summary.diagnostic_artifact_paths
    assert set(paths) == {"path_risk_window_summary", "passed_vs_failed_path_risk_summary"}
    assert Path(paths["path_risk_window_summary"]).exists()
    assert Path(paths["passed_vs_failed_path_risk_summary"]).exists()
    assert all("path_risk_diagnostics" in row.feature_artifact_paths for row in result.summary.windows)
    assert all("path_risk_threshold_summary" in row.feature_artifact_paths for row in result.summary.windows)

    with Path(paths["path_risk_window_summary"]).open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 2
    assert rows[0]["horizon_bars"] == "1"
    assert rows[0]["average_max_favorable_atr"] == "1.1"

    with Path(paths["passed_vs_failed_path_risk_summary"]).open(newline="", encoding="utf-8") as file:
        grouped = list(csv.DictReader(file))
    assert grouped
    assert grouped[0]["window_group"] == "passed"
    assert grouped[0]["fav_1p0_before_adv_1p0_ratio"] == "0.5"

    summary = json.loads(result.summary_json_path.read_text(encoding="utf-8"))
    assert summary["path_risk_diagnostics_enabled"] is True
    assert summary["diagnostic_artifact_paths"] == paths
