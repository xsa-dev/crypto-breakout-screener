## 1. OpenSpec readiness
- [x] 1.1 Confirm no active OpenSpec changes and record unrelated dirty files.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 list` showed no active changes; `git status --short --branch` showed unrelated modified `.dev/autonomous_dev.sh` before this change.
- [x] 1.2 Reconstruct the current reference scorecard and failing windows before implementation.
  - Evidence: proposal/design record `conservative-v1-m15-slope-positive-max-trades-8` as `5/8` with failed quarters `2024q1`, `2024q2`, `2024q4` from `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/2396740c76d50b91/summary.json`.
- [x] 1.3 Validate this change strictly before source implementation.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 validate compare-breakout-close-confirmed-exit-profiles --strict --no-interactive` and `validate --all --strict --no-interactive` passed.

## 2. Implementation
- [x] 2.1 Add disabled-by-default close-confirmed exit profile config fields and deterministic exit resolution.
  - Evidence: `BacktestExitProfileConfig` has `close_stop_atr`/`close_target_atr`; `_resolve_exit` returns `close_atr_stop`/`close_atr_target` from post-entry closes only.
- [x] 2.2 Add exactly the three fixed named close-confirmed exit profiles.
  - Evidence: `EXIT_PROFILE_NAMES` and `exit_profile_config` include `close-stop-0p5-hold-8`, `close-stop-1p0-hold-16`, and `close-stop-0p5-close-target-2p0-hold-16`.
- [x] 2.3 Preserve default/reference behavior and all non-exit profile settings.
  - Evidence: new profiles are selected only by explicit gate-profile names and share existing reference gates, M15 slope feature filter, and max-trades risk control.
- [x] 2.4 Ensure close-confirmed exit profile settings/counts serialize in existing batch JSON/CSV outputs.
  - Evidence: `test_batch_runner_records_exit_profile` asserts close-stop settings serialization; real summaries under `artifacts/close-confirmed-exit-profile-comparison/.../summary.json` record exit profile fields.

## 3. Tests
- [x] 3.1 Add or update backtest tests for close-confirmed stop, close-confirmed target, stop-first ordering, and missing ATR fallback.
  - Evidence: `tests/test_breakout_backtesting_reporting.py` covers close-target by close, close-stop by close while ignoring intrabar wick, and missing ATR fallback.
- [x] 3.2 Add or update batch/profile tests for the new named profile resolution.
  - Evidence: `tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile` asserts the close-stop/close-target profile resolves to the expected config.
- [x] 3.3 Run targeted tests covering close-confirmed exit settings and realistic-cost classification.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_breakout_backtesting_reporting.py::test_exit_profile_close_confirmed_stop_and_target_use_bar_closes tests/test_breakout_backtesting_reporting.py::test_exit_profile_close_confirmed_stop_is_stop_first_and_ignores_intrabar_wicks tests/test_breakout_backtesting_reporting.py::test_exit_profile_close_confirmed_missing_atr_falls_back_to_max_hold tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile tests/test_realistic_cost_profile_search.py` passed 6 tests.

## 4. Quarterly experiment loop
- [x] 4.1 Run each fixed candidate over `2023q1..2024q4` with cached public data.
  - Evidence: real quarterly batch summaries:
    - `close-stop-0p5-hold-8`: `artifacts/close-confirmed-exit-profile-comparison/conservative-v1-m15-slope-positive-max-trades-8-close-stop-0p5-hold-8/crypto/BTCUSDT/c1796885c0848b06/summary.json`
    - `close-stop-1p0-hold-16`: `artifacts/close-confirmed-exit-profile-comparison/conservative-v1-m15-slope-positive-max-trades-8-close-stop-1p0-hold-16/crypto/BTCUSDT/a2546d4180a2ecf8/summary.json`
    - `close-stop-0p5-close-target-2p0-hold-16`: `artifacts/close-confirmed-exit-profile-comparison/conservative-v1-m15-slope-positive-max-trades-8-close-stop-0p5-close-target-2p0-hold-16/crypto/BTCUSDT/841025cfc60ac9de/summary.json`
- [x] 4.2 Record baseline pass/fail scorecard for each candidate.
  - Evidence:
    - `close-stop-0p5-hold-8`: baseline `1/8`; only `2024q1` passed; remaining quarters failed mostly max drawdown, with `2024q2` also net/PF.
    - `close-stop-1p0-hold-16`: baseline `1/8`; only `2023q4` passed; remaining quarters failed max drawdown, with `2023q2` also net/PF.
    - `close-stop-0p5-close-target-2p0-hold-16`: baseline `2/8`; `2023q4` and `2024q1` passed; remaining quarters failed max drawdown and/or net/PF.
- [x] 4.3 Run realistic-cost robustness summary with `spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055`, and `funding_rate_per_bar=0.00001`.
  - Evidence: `artifacts/close-confirmed-exit-profile-comparison-summary/realistic-cost/summary.json` and `scorecard.csv`; realistic settings include `spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055`, `funding_rate_per_bar=0.00001`.
- [x] 4.4 Update tasks with per-quarter status changes, blockers, metrics, and artifact paths.
  - Evidence: this task list records baseline status changes; realistic scorecard records all per-quarter blockers.
  - Realistic scores: all three candidates `0/8`; every realistic quarter failed, mostly net/PF/drawdown blockers; no quarter changed to pass versus the realistic-cost target.
- [x] 4.5 If no candidate reaches realistic-cost `8/8`, mark the hypothesis falsified and do not send success notification.
  - Verdict: falsified. Best realistic-cost score was `0/8`; `net_costs_supported_candidates=[]`; no success notification sent.

## 5. Verification and closure
- [x] 5.1 Run targeted and full pytest as appropriate.
  - Evidence: targeted pytest passed 6 tests; final `env UV_CACHE_DIR=.uv-cache uv run pytest` passed 109 tests.
- [x] 5.2 Run `uv run ruff check .`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run ruff check .` passed.
- [x] 5.3 Run `uv run pyright`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pyright` passed with 0 errors.
- [x] 5.4 Run strict OpenSpec validation for this change and all specs.
  - Evidence: strict change validation passed; `validate --all --strict --no-interactive` passed 11 items.
- [x] 5.5 Run `git diff --check` and duplicate spec/archive-name check.
  - Evidence: `git diff --check` passed; duplicate spec/archive-name check reported `intersection_count=0` before archive.
- [x] 5.6 Perform self-review for scope, no-lookahead, threshold preservation, artifact completeness, and secret safety.
  - Review: implementation only adds explicit research-only close-confirmed exit profile settings and three named profiles; no entry filters, thresholds, private data, live trading, push/MR/merge, or success notification were used. Quarterly evidence falsifies the hypothesis (`best_realistic_passed_count=0/8`) rather than weakening criteria.
- [x] 5.7 Archive the completed change as success or falsified research evidence before commit.
  - Evidence: archived as `openspec/changes/archive/2026-06-27-compare-breakout-close-confirmed-exit-profiles` after strict validation; archive warning reflected these final closure checkboxes being completed after archive.
- [x] 5.8 Create one scoped local commit if repository state is safe.
  - Evidence: repository state is safe for a scoped commit with unrelated `.dev/autonomous_dev.sh` intentionally left unstaged; final report records the created commit hash.
