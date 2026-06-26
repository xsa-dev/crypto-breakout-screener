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
            artifact_paths=[str(metrics_path), str(manifest_path)],
        )

    return run_single
