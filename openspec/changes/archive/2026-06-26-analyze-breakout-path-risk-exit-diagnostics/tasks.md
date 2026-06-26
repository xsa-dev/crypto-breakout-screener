## 1. OpenSpec readiness
- [x] 1.1 Confirm previous `analyze-breakout-mae-mfe-holding-horizon` change is archived and committed. Evidence: previous change archived and committed as `9c78d37 [openspec analysis] analyze breakout forward path diagnostics`.
- [x] 1.2 Confirm this change is diagnostic-only and does not add or activate exits. Evidence: implementation adds opt-in path-risk report labels/artifacts only; trade selection, realized metrics, exit behavior, and verdict logic remain unchanged.
- [x] 1.3 Validate the OpenSpec change strictly before source-code implementation. Evidence: strict validation passed before implementation.

## 2. Path-risk diagnostics
- [x] 2.1 Inspect existing forward-path/report/export code from the prior change. Evidence: implementation reuses the existing report/export diagnostic pattern from forward-path artifacts.
- [x] 2.2 Add opt-in per-trade path-risk diagnostics for fixed horizons 1/2/4/8/16 M15 bars. Evidence: `BacktestConfig.path_risk_diagnostics` enables per-run `*-path-risk-diagnostics.csv`.
- [x] 2.3 Add fixed favorable/adverse ATR threshold labels without threshold optimization. Evidence: fixed defaults use +0.5/+1.0/+1.5/+2.0 ATR and -0.5/-1.0/-1.5/-2.0 ATR labels.
- [x] 2.4 Record unavailable counts/reasons when entry-time ATR or future bars are unavailable. Evidence: tests cover `missing_entry_atr` and `insufficient_future_bars`; summaries include unavailable counts.
- [x] 2.5 Ensure diagnostics are computed after trades are created and cannot influence entry/risk/exit decisions. Evidence: tests verify enabling diagnostics does not change trade selection or realized metrics.

## 3. Threshold ordering and exit-feasibility summaries
- [x] 3.1 Export favorable-before-adverse and adverse-before-favorable ordering summaries. Evidence: per-trade labels include `fav_1p0_before_adv_1p0` style fields and batch summary aggregates these ratios.
- [x] 3.2 Export break-even reachability diagnostics. Evidence: per-trade labels include `breakeven_reachable`, `breakeven_reached_bars`, and `breakeven_touched_after_reach`.
- [x] 3.3 Export trailing-touch-after-favorable-excursion diagnostics. Evidence: per-trade labels include fixed giveback labels such as `trail_after_fav_1p0_giveback_0p5_touched`.
- [x] 3.4 Keep all synthetic/feasibility labels separate from actual realized metrics and verdicts. Evidence: diagnostics are separate artifacts and batch aggregate remained unchanged from baseline.

## 4. Batch comparison artifacts
- [x] 4.1 Add opt-in batch support for path-risk diagnostics. Evidence: CLI supports `--path-risk-diagnostics`.
- [x] 4.2 Export `path-risk-window-summary.csv`. Evidence: quarterly run produced `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/2396740c76d50b91/path-risk-window-summary.csv`.
- [x] 4.3 Export `passed-vs-failed-path-risk-summary.csv`. Evidence: quarterly run produced `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/2396740c76d50b91/passed-vs-failed-path-risk-summary.csv`.
- [x] 4.4 Reference diagnostic artifact paths in batch summary JSON. Evidence: quarterly summary JSON contains both path-risk artifact paths.

## 5. Tests and verification
- [x] 5.1 Add deterministic unit tests for favorable/adverse threshold hit ordering. Evidence: reporting tests assert threshold labels and ordering fields are generated.
- [x] 5.2 Add unavailable-data tests for missing entry-time ATR and insufficient future bars. Evidence: reporting tests assert machine-readable unavailable reasons.
- [x] 5.3 Add no-lookahead tests proving diagnostics do not alter trade selection, realized metrics, or verdicts. Evidence: diagnostic-enabled report keeps the same trade selection and metrics as diagnostics-disabled report.
- [x] 5.4 Add batch artifact tests for path-risk summary outputs. Evidence: crypto batch tests assert path-risk batch artifacts and JSON references.
- [x] 5.5 Run pytest, ruff, pyright, OpenSpec validation, and `git diff --check`. Evidence before real run: `uv run pytest` passed 94 tests, `ruff check .` passed, `pyright` passed, OpenSpec strict validation passed, and `git diff --check` passed after EOF whitespace cleanup.

## 6. Real research run
- [x] 6.1 Run quarterly 2023-2024 BTCUSDT diagnostics for `conservative-v1-m15-slope-positive-max-trades-8`. Evidence: batch `2396740c76d50b91` completed with `--path-risk-diagnostics`.
- [x] 6.2 Summarize whether favorable excursion tends to occur before adverse excursion. Evidence: +1 ATR favorable-before-1 ATR adverse is not strongly dominant; failed windows range ~0.13/0.24/0.36/0.45/0.48 across horizons, passed windows ~0.15/0.27/0.39/0.47/0.50.
- [x] 6.3 Summarize whether break-even/trailing/stop-distance follow-up OpenSpecs are justified. Evidence: break-even reachability grows by horizon, but break-even touch-after-reach and trailing giveback touch rates are high; a future implementation is not justified directly, but a narrower stop/exit feasibility hypothesis could be proposed if scoped around adverse-before-favorable ordering.

## 7. Archive and commit
- [x] 7.1 Archive the OpenSpec change after tasks and verification complete. Evidence: archived as `openspec/changes/archive/2026-06-26-analyze-breakout-path-risk-exit-diagnostics/`.
- [x] 7.2 Re-run full verification after archive. Evidence: post-archive verification is run before commit.
- [x] 7.3 Commit only scoped files, excluding unrelated `.dev/autonomous_dev.sh`. Evidence: scoped commit excludes `.dev/autonomous_dev.sh`.
