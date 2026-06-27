## 1. OpenSpec readiness
- [x] 1.1 Confirm no active OpenSpec changes and record unrelated dirty files.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 list` showed no active changes before this change; `git status --short --branch` showed unrelated modified `.dev/autonomous_dev.sh`.
- [x] 1.2 Reconstruct the current reference scorecard and failing windows before implementation.
  - Evidence: proposal/design record `conservative-v1-m15-slope-positive-max-trades-8` as `5/8` with failed quarters `2024q1`, `2024q2`, `2024q4` from `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/2396740c76d50b91/summary.json`.
- [x] 1.3 Validate this change strictly before source implementation.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 validate compare-breakout-protected-partial-exit-profiles --strict --no-interactive` and `validate --all --strict --no-interactive` passed before source edits.

## 2. Implementation
- [x] 2.1 Add disabled-by-default protected residual partial-exit settings with validation for deterministic residual break-even/trailing protection.
  - Evidence: `BacktestExitProfileConfig.partial_residual_breakeven` and `partial_residual_trailing_giveback_atr` validate mutual exclusion and require `partial_targets`.
- [x] 2.2 Add exactly the three fixed named protected partial-exit profiles.
  - Evidence: `EXIT_PROFILE_NAMES` and `exit_profile_config` include the three protected partial profiles named in the proposal.
- [x] 2.3 Preserve default/reference behavior and all non-exit profile settings.
  - Evidence: new settings default to disabled/`None`; profiles are selected only by explicit gate-profile names and reuse existing reference gates, M15 slope feature filter, and max-trades risk control.
- [x] 2.4 Compute aggregate protected partial-exit PnL/costs with per-leg quantity and holding bars while preserving existing report APIs.
  - Evidence: `_resolve_partial_exit` appends residual break-even/trailing legs to the existing partial-leg aggregation path; `_partial_exit_pnl_and_costs` still computes one aggregate `BacktestTrade`.
- [x] 2.5 Ensure protected partial-exit profile settings/counts serialize in existing batch JSON/CSV outputs.
  - Evidence: exit metadata records `exit_profile_residual_protection`; `test_batch_runner_records_exit_profile` covers protected profile settings serialization.

## 3. Tests
- [x] 3.1 Add or update backtest tests for residual break-even, residual trailing, inactive-before-fill behavior, missing ATR fallback, validation, and aggregate cost/PnL accounting.
  - Evidence: `tests/test_breakout_backtesting_reporting.py` includes protected residual break-even, wait-for-fill, residual trailing, and validation assertions; existing missing ATR and cost tests still cover the shared partial path.
- [x] 3.2 Add or update batch/profile tests for the new named profile resolution and serialization.
  - Evidence: `tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile` asserts protected residual profile configs.
- [x] 3.3 Run targeted tests covering protected partial exits and realistic-cost classification.
  - Evidence: targeted pytest for four protected partial tests plus batch profile serialization passed 5 tests.

## 4. Quarterly experiment loop
- [x] 4.1 Run each fixed candidate with cached public data until a required realistic-cost quarter falsifies the candidate or all eight quarters pass.
  - Evidence: exact cached-data realistic-cost runs evaluated `2024q1` for all three candidates; each failed `2024q1`, so none can reach required `8/8`.
- [x] 4.2 Record baseline pass/fail evidence for each candidate where run before early falsification.
  - Evidence: baseline scorecards were not run after realistic `2024q1` early falsification because success requires realistic-cost `8/8`; remaining required windows are marked blocked/not run in the scorecard.
- [x] 4.3 Run realistic-cost checks with `spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055`, and `funding_rate_per_bar=0.00001`.
  - Evidence: realistic summaries under `artifacts/protected-partial-exit-profile-comparison-realistic-smoke/.../summary.json`; combined early-falsified summary at `artifacts/protected-partial-exit-profile-comparison-summary/early-falsified/summary.json`.
- [x] 4.4 Update tasks with per-quarter status changes, blockers, metrics, and artifact paths.
  - Evidence: `artifacts/protected-partial-exit-profile-comparison-summary/early-falsified/scorecard.csv` records required windows; `2024q1` is failed for every candidate and remaining quarters are marked blocked/not run after early falsification.
- [x] 4.5 If no candidate reaches realistic-cost `8/8`, mark the hypothesis falsified and do not send success notification.
  - Verdict: falsified. `partial-50-target-1p0-residual-breakeven-hold-16` realistic `2024q1` failed net/PF/drawdown (`net_profit=-50141.52`, `profit_factor=0.7996`, `max_drawdown=-3.6742`); `partial-30-50-targets-1p0-2p0-residual-breakeven-hold-16` failed (`net_profit=-67963.83`, `profit_factor=0.7457`, `max_drawdown=-4.2587`); `partial-50-target-1p0-residual-trail-1p0-giveback-1p0-hold-16` failed (`net_profit=-62895.18`, `profit_factor=0.7433`, `max_drawdown=-3.3936`). No success notification sent.

## 5. Verification and closure
- [x] 5.1 Run targeted and full pytest as appropriate.
  - Evidence: targeted pytest passed 5 tests; final `env UV_CACHE_DIR=.uv-cache uv run pytest` passed 117 tests.
- [x] 5.2 Run `uv run ruff check .`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run ruff check .` passed.
- [x] 5.3 Run `uv run pyright`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pyright` passed with 0 errors.
- [x] 5.4 Run strict OpenSpec validation for this change and all specs.
  - Evidence: strict change validation passed; `validate --all --strict --no-interactive` passed 11 items.
- [x] 5.5 Run `git diff --check` and duplicate spec/archive-name check.
  - Evidence: `git diff --check` passed; duplicate spec/archive-name check reported `intersection_count=0` before archive.
- [x] 5.6 Perform self-review for scope, no-lookahead, threshold preservation, artifact completeness, and secret safety.
  - Review: implementation only enables explicit protected partial-exit research profiles; default/reference behavior remains disabled-by-default; no entry filters, thresholds, private data, live trading, push/MR/merge, or success notification were used. Realistic-cost `2024q1` falsifies all candidates, so the score did not move toward `8/8`.
- [x] 5.7 Archive the completed change as success or falsified research evidence before commit.
  - Evidence: archived as `openspec/changes/archive/2026-06-27-compare-breakout-protected-partial-exit-profiles` after strict validation; archive warning reflected these final closure checkboxes being completed after archive.
- [x] 5.8 Create one scoped local commit if repository state is safe.
  - Evidence: repository state is safe for a scoped commit with unrelated `.dev/autonomous_dev.sh` intentionally left unstaged; final report records the commit hash.
