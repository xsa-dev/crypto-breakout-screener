import json
from pathlib import Path

import pytest

from src.app.breakout.backtesting import stable_hash
from src.app.breakout.experiments.crypto_backtest import import_crypto_csv, run_crypto_experiment

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
    assert len(first.artifact_paths) == 12
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
