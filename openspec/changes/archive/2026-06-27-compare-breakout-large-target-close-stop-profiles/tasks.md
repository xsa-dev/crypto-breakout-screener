## 1. OpenSpec readiness
- [x] 1.1 Confirm no active OpenSpec changes and record unrelated dirty files.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 list` showed no active changes before creating this change; `git status --short --branch` showed unrelated modified `.dev/autonomous_dev.sh`, intentionally left untouched.
- [x] 1.2 Reconstruct the current reference scorecard and failing windows before implementation.
  - Evidence: proposal records `conservative-v1-m15-slope-positive-max-trades-8` as `5/8` with failed quarters `2024q1`, `2024q2`, and `2024q4` from `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/2396740c76d50b91/summary.json`.
- [x] 1.3 Validate this change strictly before source implementation.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 validate compare-breakout-large-target-close-stop-profiles --strict --no-interactive` and `validate --all --strict --no-interactive` passed.

## 2. Implementation
- [x] 2.1 Add exactly the three fixed named large-target close-stop profiles.
  - Evidence: `EXIT_PROFILE_NAMES` and `exit_profile_config` include the three profiles from the proposal.
- [x] 2.2 Preserve default/reference behavior and all non-selected profile settings.
  - Evidence: default exit profile remains unchanged; the new settings are only returned for explicit names.
- [x] 2.3 Serialize close-stop/target/holding settings and exit reasons in existing batch artifacts.
  - Evidence: `test_batch_runner_records_exit_profile` asserts selected profile JSON contains `fixed_holding_bars`, `target_atr`, and `close_stop_atr`; existing report metadata emits close stop/target fields and exit reasons.

## 3. Tests
- [x] 3.1 Add or update batch/profile tests for named profile resolution and serialization.
  - Evidence: `tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile` covers the new large-target close-stop mapping and summary serialization.
- [x] 3.2 Run targeted tests covering the new profile mapping and existing close-stop-first behavior.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile tests/test_breakout_backtesting_reporting.py::test_exit_profile_close_target_only_uses_closes tests/test_breakout_backtesting_reporting.py::test_exit_profile_uses_conservative_same_bar_stop_first` passed 3 tests.

## 4. Quarterly experiment loop
- [x] 4.1 Run each fixed candidate with cached public data until a required realistic-cost quarter falsifies the candidate or all eight quarters pass.
  - Evidence: exact cached-data realistic-cost runs evaluated `2024q1` for all three candidates; each failed `2024q1` on `max_drawdown_below_threshold`, so none can reach required `8/8`.
- [x] 4.2 Record baseline or realistic pass/fail evidence for each candidate as required by the success gate.
  - Evidence: baseline scorecards were not run after realistic `2024q1` early falsification because success requires realistic-cost `8/8`; remaining required windows are marked blocked/not run in the scorecard.
- [x] 4.3 Run realistic-cost checks with `spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055`, and `funding_rate_per_bar=0.00001`.
  - Evidence: realistic summaries under `artifacts/large-target-close-stop-profile-comparison-realistic-smoke/.../summary.json`; combined early-falsified summary at `artifacts/large-target-close-stop-profile-comparison-summary/early-falsified/summary.json`.
- [x] 4.4 Update tasks with per-quarter status changes, blockers, metrics, and artifact paths.
  - Evidence: `artifacts/large-target-close-stop-profile-comparison-summary/early-falsified/scorecard.csv` records all required windows; `2024q1` is failed for every candidate and remaining quarters are marked blocked/not run after early falsification.
- [x] 4.5 If no candidate reaches realistic-cost `8/8`, mark the hypothesis falsified and do not send success notification.
  - Verdict: falsified. `target-3p0-close-stop-1p0-hold-32` realistic `2024q1` failed drawdown (`net_profit=192930.95`, `profit_factor=1.5554`, `max_drawdown=-0.7807`); `target-4p0-close-stop-1p0-hold-32` failed drawdown (`net_profit=152286.99`, `profit_factor=1.4159`, `max_drawdown=-0.8824`); `close-target-2p0-close-stop-1p0-hold-32` failed drawdown (`net_profit=136480.57`, `profit_factor=1.3881`, `max_drawdown=-1.5708`). No success notification sent.

## 5. Verification and closure
- [x] 5.1 Run targeted and full pytest as appropriate.
  - Evidence: targeted pytest passed 3 tests; final `env UV_CACHE_DIR=.uv-cache uv run pytest` passed 119 tests.
- [x] 5.2 Run `uv run ruff check .`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run ruff check .` passed.
- [x] 5.3 Run `uv run pyright`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pyright` passed with 0 errors.
- [x] 5.4 Run strict OpenSpec validation for this change and all specs.
  - Evidence: strict change validation passed; `validate --all --strict --no-interactive` passed 11 items.
- [x] 5.5 Run `git diff --check` and duplicate spec/archive-name check.
  - Evidence: `git diff --check` passed; duplicate spec/archive-name check reported `intersection_count=0` before archive.
- [x] 5.6 Perform self-review for scope, no-lookahead, threshold preservation, artifact completeness, and secret safety.
  - Review: implementation only adds three disabled-by-default explicit research-only exit-profile mappings; close-stop and target decisions use existing post-entry M15 bars and entry-time ATR, with no entry/filter/threshold/cost/private-data changes. Realistic `2024q1` early-falsified every candidate on max drawdown, so the score did not reach `8/8` and no success notification was sent.
- [x] 5.7 Archive the completed change as success or falsified research evidence before commit.
  - Evidence: archived as `openspec/changes/archive/2026-06-27-compare-breakout-large-target-close-stop-profiles`; archive warnings were non-blocking (`Why` length and closure checkboxes completed after archive).
- [x] 5.8 Create one scoped local commit if repository state is safe.
  - Evidence: repository state is safe for a scoped commit with unrelated `.dev/autonomous_dev.sh` intentionally left unstaged; final report records the created commit hash.
