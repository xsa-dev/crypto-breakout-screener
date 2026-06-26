import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from src.app.breakout.backtesting import stable_hash
from src.app.breakout.experiments import crypto_backtest
from src.app.breakout.experiments.crypto_backtest import (
    REQUIRED_DOWNLOAD_TIMEFRAMES,
    download_bybit_public_ohlcv_sync,
    import_crypto_csv,
    main,
    run_crypto_experiment,
)

FIXTURE = Path(__file__).parent / "fixtures" / "btcusdt_m15.csv"


def test_crypto_csv_import_normalizes_deduplicates_orders_and_detects_gaps(tmp_path) -> None:
    csv_path = tmp_path / "unordered.csv"
    csv_path.write_text(
        "timestamp,open,high,low,close,volume\n"
        "2026-01-01T00:30:00Z,102,103,101,102,12\n"
        "2026-01-01T00:00:00Z,100,101,99,100,10\n"
        "2026-01-01T00:00:00Z,100,102,99,101,11\n"
        "2026-01-01T01:00:00Z,103,104,102,103,13\n",
        encoding="utf-8",
    )

    imported = import_crypto_csv(csv_path)

    assert [bar["ts"].isoformat() for bar in imported.bars] == [
        "2026-01-01T00:00:00+00:00",
        "2026-01-01T00:30:00+00:00",
        "2026-01-01T01:00:00+00:00",
    ]
    assert imported.bars[0]["close"] == 101
    assert imported.bars[0]["symbol"] == "BTCUSDT"
    assert imported.bars[0]["timeframe"] == "M15"
    assert imported.warnings == ["duplicate_bars_last_row_wins:1", "input_rows_out_of_order_sorted"]
    assert len(imported.gaps) == 2
    assert imported.gaps[0]["expected_seconds"] == 900
    assert imported.gaps[0]["actual_seconds"] == 1800
    assert stable_hash(imported.bars) == stable_hash(import_crypto_csv(csv_path).bars)


def test_crypto_csv_import_rejects_invalid_ohlc(tmp_path) -> None:
    csv_path = tmp_path / "invalid.csv"
    csv_path.write_text(
        "timestamp,open,high,low,close,volume\n"
        "2026-01-01T00:00:00Z,100,99,98,100,10\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="high is below"):
        import_crypto_csv(csv_path)


def test_crypto_runner_writes_manifest_report_artifacts_and_omits_private_env(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("BYBIT_API_KEY", "SHOULD_NOT_APPEAR")
    monkeypatch.setenv("BYBIT_API_SECRET", "SHOULD_NOT_APPEAR")

    first = run_crypto_experiment(csv_path=FIXTURE, output_dir=tmp_path)
    second = run_crypto_experiment(csv_path=FIXTURE, output_dir=tmp_path)

    assert first.run_id == second.run_id
    assert first.dataset_hash == second.dataset_hash
    assert first.config_hash == second.config_hash
    assert first.symbol == "BTCUSDT"
    assert first.timeframe == "M15"
    assert first.bar_count == 12
    assert first.trade_count >= 1
    assert first.manifest_path.exists()
    assert len(first.artifact_paths) == 16
    assert any(path.endswith("-daily-summary.csv") for path in first.artifact_paths)
    assert any(path.endswith("-weekly-summary.csv") for path in first.artifact_paths)
    assert any(path.endswith("-lifecycle-diagnostics.csv") for path in first.artifact_paths)
    assert any(path.endswith("-score-bucket-pnl.csv") for path in first.artifact_paths)
    assert first.artifact_paths[-1].endswith("-dataset-manifest.json")

    manifest_text = first.manifest_path.read_text(encoding="utf-8")
    assert "SHOULD_NOT_APPEAR" not in manifest_text
    manifest = json.loads(manifest_text)
    assert manifest["market"] == "crypto"
    assert manifest["instrument_type"] == "perpetual"
    assert manifest["requested_context_timeframes"] == ["H1", "H4", "D1"]
    assert manifest["available_context_timeframes"] == []
    assert set(manifest["unavailable_context_timeframes"]) == {"H1", "H4", "D1"}
    assert manifest["dataset_hash"] == first.dataset_hash
    assert manifest["report_run_id"] == first.run_id
    assert manifest["limitations"]["production_approval"].startswith("research artifact only")
    assert "funding" in manifest["limitations"]

    report_path = first.artifact_dir / f"{first.run_id}.json"
    report_text = report_path.read_text(encoding="utf-8")
    assert "SHOULD_NOT_APPEAR" not in report_text
    report = json.loads(report_text)
    assert str(first.manifest_path) in report["artifact_paths"]
    assert report["unavailable_reasons"]["production_approval"].startswith(
        "research artifact only"
    )

    for artifact_path in first.artifact_paths:
        assert Path(artifact_path).exists()


def test_crypto_runner_keeps_first_slice_scope() -> None:
    with pytest.raises(ValueError, match="BTCUSDT only"):
        run_crypto_experiment(csv_path=FIXTURE, symbol="ETHUSDT")
    with pytest.raises(ValueError, match="M15 only"):
        run_crypto_experiment(csv_path=FIXTURE, timeframe="H1")


def test_bybit_public_downloader_writes_all_timeframe_csvs_and_metadata(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("BYBIT_API_KEY", "SHOULD_NOT_APPEAR")
    calls: list[dict[str, str]] = []

    async def fake_request(*, session, params, timeout_seconds, max_retries):
        del session, timeout_seconds, max_retries
        calls.append(params)
        interval_seconds = {"15": 900, "60": 3600, "240": 14400, "D": 86400}[
            params["interval"]
        ]
        start_ms = int(params["start"])
        end_ms = int(params["end"])
        rows = []
        current_ms = start_ms
        while current_ms <= end_ms:
            index = current_ms // (interval_seconds * 1000)
            open_price = 100_000 + index
            rows.append(
                [
                    str(current_ms),
                    str(open_price),
                    str(open_price + 10),
                    str(open_price - 10),
                    str(open_price + 5),
                    str(100 + index),
                    "0",
                ]
            )
            current_ms += interval_seconds * 1000
        # Bybit can return newest-first; duplicate the oldest row to exercise de-dupe.
        if rows:
            rows = list(reversed(rows)) + [rows[0]]
        return {"retCode": 0, "retMsg": "OK", "result": {"list": rows}}

    monkeypatch.setattr(crypto_backtest, "_request_bybit_public_json", fake_request)

    result = download_bybit_public_ohlcv_sync(
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 1, 2, 45, tzinfo=UTC),
        output_dir=tmp_path / "market-data",
        limit=2,
    )

    assert set(result.csv_paths) == set(REQUIRED_DOWNLOAD_TIMEFRAMES)
    assert {call["interval"] for call in calls} == {"15", "60", "240", "D"}
    assert "SHOULD_NOT_APPEAR" not in result.model_dump_json()
    m15 = import_crypto_csv(result.csv_paths["M15"], timeframe="M15")
    h1 = import_crypto_csv(result.csv_paths["H1"], timeframe="H1")
    h4 = import_crypto_csv(result.csv_paths["H4"], timeframe="H4")
    d1 = import_crypto_csv(result.csv_paths["D1"], timeframe="D1")
    assert len(m15.bars) == 12
    assert len(h1.bars) == 3
    assert len(h4.bars) == 1
    assert len(d1.bars) == 1
    assert [bar["ts"] for bar in m15.bars] == sorted(bar["ts"] for bar in m15.bars)
    assert stable_hash(m15.bars) == stable_hash(
        import_crypto_csv(result.csv_paths["M15"], timeframe="M15").bars
    )
    assert result.source_metadata["timeframe_metadata"]["M15"]["page_count"] == 6


def test_download_and_run_records_public_source_and_context_paths(tmp_path, monkeypatch) -> None:
    async def fake_request(*, session, params, timeout_seconds, max_retries):
        del session, timeout_seconds, max_retries
        interval_seconds = {"15": 900, "60": 3600, "240": 14400, "D": 86400}[
            params["interval"]
        ]
        start_ms = int(params["start"])
        end_ms = int(params["end"])
        rows = []
        current_ms = start_ms
        while current_ms <= end_ms:
            index = current_ms // (interval_seconds * 1000)
            price = 99_000 + index * (10 if params["interval"] == "15" else 1)
            rows.append(
                [
                    str(current_ms),
                    str(price),
                    str(price + 1000),
                    str(price - 1000),
                    str(price + 500),
                    "100",
                    "0",
                ]
            )
            current_ms += interval_seconds * 1000
        return {"retCode": 0, "retMsg": "OK", "result": {"list": list(reversed(rows))}}

    monkeypatch.setattr(crypto_backtest, "_request_bybit_public_json", fake_request)

    exit_code = main(
        [
            "--download-public",
            "bybit",
            "--start",
            "2026-01-01T00:00:00Z",
            "--end",
            "2026-01-01T02:45:00Z",
            "--download-limit",
            "20",
            "--market-data-dir",
            str(tmp_path / "market-data"),
            "--output-dir",
            str(tmp_path / "backtests"),
        ]
    )

    assert exit_code == 0
    manifest_paths = list((tmp_path / "backtests").glob("**/*-dataset-manifest.json"))
    assert len(manifest_paths) == 1
    manifest_text = manifest_paths[0].read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)
    assert manifest["source"] == "bybit_public"
    assert set(manifest["available_context_timeframes"]) == {"H1", "H4", "D1"}
    assert set(manifest["context_dataset_paths"]) == {"H1", "H4", "D1"}
    assert set(manifest["source_metadata"]["csv_paths"]) == {"M15", "H1", "H4", "D1"}


def test_public_downloader_validates_inputs_and_errors(tmp_path, monkeypatch) -> None:
    with pytest.raises(ValueError, match="BTCUSDT only"):
        download_bybit_public_ohlcv_sync(
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 2, tzinfo=UTC),
            symbol="ETHUSDT",
            output_dir=tmp_path,
        )
    with pytest.raises(ValueError, match="requires M15,H1,H4,D1"):
        download_bybit_public_ohlcv_sync(
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 2, tzinfo=UTC),
            timeframes=("M15",),
            output_dir=tmp_path,
        )

    async def empty_request(*, session, params, timeout_seconds, max_retries):
        del session, params, timeout_seconds, max_retries
        return {"retCode": 0, "retMsg": "OK", "result": {"list": []}}

    monkeypatch.setattr(crypto_backtest, "_request_bybit_public_json", empty_request)
    with pytest.raises(ValueError, match="returned no closed rows"):
        download_bybit_public_ohlcv_sync(
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 2, tzinfo=UTC),
            output_dir=tmp_path,
        )

    async def provider_error(*, session, params, timeout_seconds, max_retries):
        del session, params, timeout_seconds, max_retries
        msg = "Bybit public kline error retCode=10001: bad request"
        raise RuntimeError(msg)

    monkeypatch.setattr(crypto_backtest, "_request_bybit_public_json", provider_error)
    with pytest.raises(RuntimeError, match="retCode=10001"):
        download_bybit_public_ohlcv_sync(
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 2, tzinfo=UTC),
            output_dir=tmp_path,
        )

    async def malformed_payload(*, session, params, timeout_seconds, max_retries):
        del session, params, timeout_seconds, max_retries
        return {"retCode": 0, "retMsg": "OK", "result": {"list": [["bad-row"]]}}

    monkeypatch.setattr(crypto_backtest, "_request_bybit_public_json", malformed_payload)
    with pytest.raises(ValueError, match="row is malformed"):
        download_bybit_public_ohlcv_sync(
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 2, tzinfo=UTC),
            output_dir=tmp_path,
        )
