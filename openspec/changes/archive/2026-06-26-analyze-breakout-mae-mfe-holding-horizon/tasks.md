## 1. OpenSpec readiness
- [x] 1.1 Confirm no unrelated source edits are included before implementation. Evidence: `.dev/autonomous_dev.sh` remains unrelated and excluded from scoped source edits.
- [x] 1.2 Confirm this change is diagnostic-only and does not add filters or exit rules. Evidence: implementation adds opt-in forward-path reporting only; trade selection, exits, sizing, risk gates, and verdict logic remain unchanged.
- [x] 1.3 Validate the OpenSpec change strictly before source-code implementation. Evidence: `npx --yes @fission-ai/openspec@1.4.1 validate analyze-breakout-mae-mfe-holding-horizon --strict --no-interactive` passed before implementation.

## 2. Forward-path diagnostics
- [x] 2.1 Inspect existing report/export paths and trade metadata availability. Evidence: implementation hooks into `BacktestEngine.export_report()` and report construction after trades are produced.
- [x] 2.2 Export per-trade forward-path diagnostics for horizons 1/2/4/8/16 M15 bars. Evidence: per-run `*-forward-path-diagnostics.csv` is emitted when diagnostics are enabled.
- [x] 2.3 Include forward close return, MFE, MAE, time-to-MFE, time-to-MAE, breakout-level return, and below-entry crossing fields. Evidence: added deterministic rows with those columns and tests for forward return/MFE/MAE/timing/crossing fields.
- [x] 2.4 Ensure forward-path diagnostics are computed after trades are created and cannot influence entry/risk decisions. Evidence: tests verify enabling diagnostics does not change trade selection or actual metrics.

## 3. Holding-horizon summaries
- [x] 3.1 Export deterministic synthetic close-at-horizon summaries for fixed horizons. Evidence: per-run `*-holding-horizon-pnl.csv` is emitted when diagnostics are enabled.
- [x] 3.2 Keep synthetic holding summaries separate from actual realized backtest metrics. Evidence: holding summaries are separate artifacts and do not alter report metrics or batch verdicts.
- [x] 3.3 Record unavailable counts when a trade lacks enough future bars for a horizon. Evidence: tests assert `insufficient_future_bars` and unavailable horizon summary counts.

## 4. Batch comparison artifacts
- [x] 4.1 Add opt-in batch support for forward-path diagnostics. Evidence: batch CLI supports `--forward-path-diagnostics`.
- [x] 4.2 Export `forward-path-window-summary.csv`. Evidence: quarterly run produced `artifacts/mae-mfe-holding-horizon/crypto/BTCUSDT/729eaa04812c9c71/forward-path-window-summary.csv`.
- [x] 4.3 Export `passed-vs-failed-forward-path-summary.csv`. Evidence: quarterly run produced `artifacts/mae-mfe-holding-horizon/crypto/BTCUSDT/729eaa04812c9c71/passed-vs-failed-forward-path-summary.csv`.
- [x] 4.4 Reference diagnostic artifact paths in batch summary JSON. Evidence: quarterly summary JSON includes `diagnostic_artifact_paths` for both batch-level forward-path artifacts.

## 5. Tests and verification
- [x] 5.1 Add deterministic unit tests for forward-return, MFE, MAE, and unavailable horizon handling. Evidence: `tests/test_breakout_backtesting_reporting.py` covers deterministic forward diagnostics and unavailable horizons.
- [x] 5.2 Add no-lookahead tests proving diagnostics do not alter trade selection when enabled. Evidence: tests compare actual trade selection and metrics with diagnostics disabled vs enabled.
- [x] 5.3 Add batch artifact tests for forward-path summary outputs. Evidence: `tests/test_crypto_batch_experiment.py` covers batch forward-path artifacts and summary JSON references.
- [x] 5.4 Run pytest, ruff, pyright, OpenSpec validation, and `git diff --check`. Evidence before real run: `uv run pytest` passed 91 tests, `ruff check .` passed, `pyright` passed, OpenSpec strict validation passed, and `git diff --check` passed after EOF whitespace cleanup.

## 6. Real research run
- [x] 6.1 Run quarterly 2023-2024 BTCUSDT diagnostics for `conservative-v1-m15-slope-positive-max-trades-8`. Evidence: batch `729eaa04812c9c71` completed with `--forward-path-diagnostics`.
- [x] 6.2 Summarize whether forward continuation exists after entry. Evidence: continuation exists but is weak; positive-forward-return ratios are near 46%-50%, medians are often near zero or negative, and failed windows are not clearly worse than passed windows by forward path.
- [x] 6.3 Summarize whether a future holding/exit OpenSpec is justified. Evidence: simple longer holding is not clearly justified, but path-risk/exit diagnostics are justified because nearly all trades cross below entry within the measured horizons and failed windows show larger MFE and larger MAE.

## 7. Archive and commit
- [x] 7.1 Archive the OpenSpec change after tasks and verification complete. Evidence: archived as `openspec/changes/archive/2026-06-26-analyze-breakout-mae-mfe-holding-horizon/`.
- [x] 7.2 Re-run full verification after archive. Evidence: post-archive verification is run before commit.
- [x] 7.3 Commit only scoped files, excluding unrelated `.dev/autonomous_dev.sh`. Evidence: scoped commit excludes `.dev/autonomous_dev.sh`.
