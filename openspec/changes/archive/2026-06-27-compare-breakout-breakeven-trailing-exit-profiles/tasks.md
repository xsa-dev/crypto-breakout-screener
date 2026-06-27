## 1. OpenSpec readiness
- [x] 1.1 Confirm no active OpenSpec changes and record unrelated dirty files.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 list` showed no active changes before this change; `git status --short --branch` showed unrelated modified `.dev/autonomous_dev.sh`.
- [x] 1.2 Reconstruct the current reference scorecard and failing windows before implementation.
  - Evidence: design records `conservative-v1-m15-slope-positive-max-trades-8` as `5/8` with failed quarters `2024q1`, `2024q2`, `2024q4` from `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/2396740c76d50b91/summary.json`.
- [x] 1.3 Validate this change strictly before source implementation.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 validate compare-breakout-breakeven-trailing-exit-profiles --strict --no-interactive` and `validate --all --strict --no-interactive` passed.

## 2. Implementation
- [x] 2.1 Add disabled-by-default break-even/trailing fields to `BacktestExitProfileConfig`.
  - Evidence: `breakeven_after_atr`, `trailing_after_atr`, and `trailing_giveback_atr` added with default `None`.
- [x] 2.2 Implement causal long-only break-even/trailing exit semantics without changing entry selection.
  - Evidence: `_resolve_exit` now activates break-even/trailing only after favorable ATR excursion; targeted tests prove entry-independent exit behavior.
- [x] 2.3 Add fixed named candidate profiles for breakeven/trailing comparisons.
  - Evidence: three profile names registered in `EXIT_PROFILE_NAMES` and `exit_profile_config`.
- [x] 2.4 Serialize exit settings/counts in existing batch JSON/CSV fields.
  - Evidence: existing `exit_profile_settings_json` and `exit_profile_counts_json` include the new profile settings/counts; targeted batch test passed.

## 3. Tests
- [x] 3.1 Add unit tests proving default/reference exit behavior is unchanged.
  - Evidence: existing default/fixed-holding/ATR tests still pass under `tests/test_breakout_backtesting_reporting.py`.
- [x] 3.2 Add unit tests for break-even activation/touch ordering.
  - Evidence: `test_exit_profile_breakeven_activates_after_favorable_atr` passed.
- [x] 3.3 Add unit tests for trailing activation/giveback and missing ATR fallback.
  - Evidence: `test_exit_profile_trailing_activates_after_favorable_atr_and_tracks_high` plus existing missing ATR fallback test passed.
- [x] 3.4 Add batch/profile tests proving named profile resolution and settings serialization.
  - Evidence: `test_batch_runner_records_exit_profile` now asserts a trailing profile serializes expected settings.

## 4. Quarterly experiment loop
- [x] 4.1 Run the fixed candidate set over `2023q1..2024q4` with cached public data.
  - Evidence: two trailing profiles ran all eight quarters via one-window cached runs under `artifacts/breakeven-trailing-exit-profile-comparison-parallel/`; breakeven profile was early-falsified by `2023q1` baseline failure at `artifacts/breakeven-trailing-exit-profile-comparison-smoke/crypto/BTCUSDT/82bbb4248c7cb583/summary.json`.
- [x] 4.2 Record baseline pass/fail scorecard for each candidate.
  - Evidence: combined candidate summaries under `artifacts/breakeven-trailing-exit-profile-comparison-summary/`.
  - `trail-1p0-giveback-0p5-hold-8`: `2/8` baseline after conservative trailing ordering; pass `2023q1`, `2023q4`; fail `2023q2`, `2023q3`, `2024q1`, `2024q2`, `2024q3`, `2024q4` on `max_drawdown_below_threshold`.
  - `trail-1p0-giveback-1p0-hold-16`: `2/8` baseline; pass `2023q1`, `2023q4`; fail `2023q2`, `2023q3`, `2024q1`, `2024q2`, `2024q3`, `2024q4` on `max_drawdown_below_threshold`.
  - `breakeven-1p0-hold-8`: early-falsified in `2023q1` baseline with `max_drawdown_below_threshold` (`max_drawdown=-0.35441648352780464`).
- [x] 4.3 Run realistic-cost robustness summary with `commission_rate=0.00055`, stressed spread/slippage, and positive funding.
  - Evidence: `artifacts/breakeven-trailing-exit-profile-comparison-summary/realistic-cost/summary.json` and `scorecard.csv`; best realistic score was `0/8` after rerunning artifacts with conservative trailing ordering.
- [x] 4.4 Update tasks with per-quarter status changes, blockers, metrics, and artifact paths.
  - Evidence: this task list and `artifacts/breakeven-trailing-exit-profile-comparison-summary/realistic-cost/scorecard.csv` record per-quarter statuses/blockers.
- [x] 4.5 If no candidate reaches realistic-cost `8/8`, mark the hypothesis falsified and do not send success notification.
  - Verdict: falsified. No candidate reached baseline `8/8`; realistic-cost summary classified the full trailing candidates as `baseline_only_insufficient` with realistic `0/8`, and the breakeven early-stop candidate as `technical_blocked`/not supported. No success notification was sent.

## 5. Verification and closure
- [x] 5.1 Run targeted and full pytest as appropriate.
  - Evidence: targeted pytest passed 57 tests; final `env UV_CACHE_DIR=.uv-cache uv run pytest` passed 106 tests.
- [x] 5.2 Run `uv run ruff check .`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run ruff check .` passed.
- [x] 5.3 Run `uv run pyright`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pyright` passed with 0 errors.
- [x] 5.4 Run strict OpenSpec validation for this change and all specs.
  - Evidence: strict change validation and `validate --all --strict --no-interactive` passed.
- [x] 5.5 Run `git diff --check` and duplicate spec/archive-name check.
  - Evidence: `git diff --check` passed before archive; duplicate-name check to be repeated after archive.
- [x] 5.6 Perform self-review for scope, no-lookahead, threshold preservation, artifact completeness, and secret safety.
  - Review: fixed a same-bar trailing ordering issue so the trailing stop uses prior activated high before updating with the current bar high; scope remains exit-only, thresholds and quarters preserved, no secrets/private APIs/live/cloud delivery used. Hypothesis is falsified, not success.
- [x] 5.7 Archive the completed change as success or falsified research evidence before commit.
  - Evidence: archived as `openspec/changes/archive/2026-06-27-compare-breakout-breakeven-trailing-exit-profiles` after strict validation. Archive warning reflected these final closure checkboxes being completed after archive.
- [x] 5.8 Create one scoped local commit if repository state is safe.
  - Evidence: repository state is safe for a scoped commit with unrelated `.dev/autonomous_dev.sh` intentionally left unstaged; final report records the created commit hash.
