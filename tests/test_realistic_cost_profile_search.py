import csv
import json
from pathlib import Path

from src.app.breakout.experiments.realistic_cost_profile_search import (
    REQUIRED_QUARTERS,
    run_realistic_cost_profile_search,
)


def test_realistic_cost_profile_search_falsifies_baseline_only_candidate(tmp_path: Path) -> None:
    source_summary = _write_candidate_summary(tmp_path, gross_pnl=1.0, include_trades=True)

    result = run_realistic_cost_profile_search(
        candidate_summary_paths=[source_summary],
        output_dir=tmp_path / "search",
    )

    summary = result.summaries[0]
    assert summary.candidate == "candidate-low-edge"
    assert summary.baseline_passed_count == 8
    assert summary.realistic_passed_count == 0
    assert summary.classification == "falsified_realistic_costs"
    assert summary.realistic_cost_model_settings["commission_rate"] == 0.00055
    assert summary.realistic_cost_model_settings["funding_rate_per_bar"] > 0
    assert summary.blockers[0].startswith("2023q1:net_profit_below_threshold")

    combined = json.loads(result.summary_json_path.read_text(encoding="utf-8"))
    assert combined["best_realistic_passed_count"] == 0
    assert combined["net_costs_supported_candidates"] == []

    with result.scorecard_csv_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 16
    realistic_rows = [row for row in rows if row["cost_scenario"] == "realistic"]
    assert {row["status"] for row in realistic_rows} == {"blocked"}
    assert all("net_profit_below_threshold" in row["blockers"] for row in realistic_rows)


def test_realistic_cost_profile_search_records_technical_blocker_for_missing_trade_ledger(
    tmp_path: Path,
) -> None:
    source_summary = _write_candidate_summary(tmp_path, gross_pnl=1_000.0, include_trades=False)

    result = run_realistic_cost_profile_search(
        candidate_summary_paths=[source_summary],
        output_dir=tmp_path / "search",
    )

    summary = result.summaries[0]
    assert summary.classification == "technical_blocked"
    assert summary.realistic_passed_count == 0
    assert all(row.status == "unknown" for row in summary.realistic_windows)
    assert all("missing_source_trade_ledger" in row.blockers for row in summary.realistic_windows)


def _write_candidate_summary(tmp_path: Path, *, gross_pnl: float, include_trades: bool) -> Path:
    windows = []
    for label in REQUIRED_QUARTERS:
        artifact_dir = tmp_path / label
        artifact_dir.mkdir(parents=True)
        run_id = f"{label}-run"
        if include_trades:
            _write_trades(artifact_dir / f"{run_id}-trades.csv", gross_pnl=gross_pnl)
        windows.append(
            {
                "window_label": label,
                "status": "passed",
                "blockers": [],
                "trade_count": 1,
                "net_profit": gross_pnl,
                "profit_factor": 2.0,
                "max_drawdown": 0.0,
                "feed_gap_count": 0,
                "artifact_dir": str(artifact_dir),
                "run_id": run_id,
            }
        )
    summary = {
        "gate_profile": "candidate-low-edge",
        "exit_profile": "none",
        "cost_model_settings": {
            "spread": 0.1,
            "slippage_per_unit": 0.02,
            "commission_per_unit": 0.01,
            "funding_per_bar": 0.0,
            "commission_rate": 0.0,
            "funding_rate_per_bar": 0.0,
        },
        "windows": windows,
    }
    path = tmp_path / "source-summary.json"
    path.write_text(json.dumps(summary), encoding="utf-8")
    return path


def _write_trades(path: Path, *, gross_pnl: float) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "trade_id",
                "entry_price",
                "exit_price",
                "quantity",
                "gross_pnl",
                "total_cost",
                "net_pnl",
                "holding_bars",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "trade_id": "t1",
                "entry_price": 50_000.0,
                "exit_price": 50_100.0,
                "quantity": 4.0,
                "gross_pnl": gross_pnl,
                "total_cost": 0.0,
                "net_pnl": gross_pnl,
                "holding_bars": 1,
            }
        )
