## 1. OpenSpec readiness
- [x] 1.1 Confirm no active OpenSpec changes and record unrelated dirty files.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 list` showed no active changes; `git status --short --branch` showed unrelated modified `.dev/autonomous_dev.sh` before this change.
- [x] 1.2 Reconstruct the current reference scorecard and failing windows before implementation.
  - Evidence: design records `conservative-v1-m15-slope-positive-max-trades-8` as `5/8` with failed quarters `2024q1`, `2024q2`, `2024q4` from `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/2396740c76d50b91/summary.json`.
- [x] 1.3 Validate this change strictly before source implementation.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 validate compare-breakout-asymmetric-atr-exit-profiles --strict --no-interactive` and `validate --all --strict --no-interactive` passed.

## 2. Implementation
- [x] 2.1 Add fixed named asymmetric ATR stop/target exit profiles for the three approved candidates.
  - Evidence: `EXIT_PROFILE_NAMES` and `exit_profile_config` include `stop-0p25-target-2p0-hold-8`, `stop-0p5-target-2p0-hold-8`, and `stop-0p75-target-2p5-hold-16`.
- [x] 2.2 Preserve default/reference exit behavior and all non-exit profile settings.
  - Evidence: new profiles are selected only by explicit gate-profile names; default/reference profile resolution remains unchanged.
- [x] 2.3 Ensure exit profile settings/counts serialize in existing batch JSON/CSV outputs.
  - Evidence: `test_batch_runner_records_exit_profile` asserts named settings serialization; real summaries under `artifacts/asymmetric-atr-exit-profile-comparison/.../summary.json` record exit profile fields.

## 3. Tests
- [x] 3.1 Add or update batch/profile tests for the new named profile resolution.
  - Evidence: `tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile` asserts `stop-0p25-target-2p0-hold-8` resolves to `fixed_holding_bars=8`, `stop_atr=0.25`, `target_atr=2.0`.
- [x] 3.2 Run targeted tests covering exit profile settings and realistic-cost classification.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile tests/test_realistic_cost_profile_search.py` passed 3 tests.

## 4. Quarterly experiment loop
- [x] 4.1 Run each fixed candidate over `2023q1..2024q4` with cached public data.
  - Evidence: real quarterly batch summaries:
    - `stop-0p25-target-2p0-hold-8`: `artifacts/asymmetric-atr-exit-profile-comparison/conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p25-target-2p0-hold-8/crypto/BTCUSDT/fcaf85601e9353a4/summary.json`
    - `stop-0p5-target-2p0-hold-8`: `artifacts/asymmetric-atr-exit-profile-comparison/conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p5-target-2p0-hold-8/crypto/BTCUSDT/4da29787842f43b7/summary.json`
    - `stop-0p75-target-2p5-hold-16`: `artifacts/asymmetric-atr-exit-profile-comparison/conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p75-target-2p5-hold-16/crypto/BTCUSDT/ec4ff3d9d78b9deb/summary.json`
- [x] 4.2 Record baseline pass/fail scorecard for each candidate.
  - Evidence:
    - `stop-0p25-target-2p0-hold-8`: baseline `3/8`; passed `2023q2`, `2023q3`, `2023q4`; failed `2023q1`, `2024q1`, `2024q2`, `2024q3`, `2024q4`.
    - `stop-0p5-target-2p0-hold-8`: baseline `3/8`; passed `2023q2`, `2023q3`, `2023q4`; failed `2023q1`, `2024q1`, `2024q2`, `2024q3`, `2024q4`.
    - `stop-0p75-target-2p5-hold-16`: baseline `3/8`; passed `2023q1`, `2023q4`, `2024q3`; failed `2023q2`, `2023q3`, `2024q1`, `2024q2`, `2024q4`.
- [x] 4.3 Run realistic-cost robustness summary with `commission_rate=0.00055`, stressed spread/slippage, and positive funding.
  - Evidence: `artifacts/asymmetric-atr-exit-profile-comparison-summary/realistic-cost/summary.json` and `scorecard.csv`; realistic settings include `spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055`, `funding_rate_per_bar=0.00001`.
- [x] 4.4 Update tasks with per-quarter status changes, blockers, metrics, and artifact paths.
  - Evidence: this task list records baseline status changes; realistic scorecard records all per-quarter blockers.
  - Realistic scores: all three candidates `0/8`; every realistic quarter failed at least net/PF/drawdown or drawdown blockers.
- [x] 4.5 If no candidate reaches realistic-cost `8/8`, mark the hypothesis falsified and do not send success notification.
  - Verdict: falsified. Best realistic-cost score was `0/8`; no `net_costs_supported_candidates`; no success notification sent.

## 5. Verification and closure
- [x] 5.1 Run targeted and full pytest as appropriate.
  - Evidence: targeted pytest passed 3 tests; final `env UV_CACHE_DIR=.uv-cache uv run pytest` passed 106 tests.
- [x] 5.2 Run `uv run ruff check .`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run ruff check .` passed.
- [x] 5.3 Run `uv run pyright`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pyright` passed with 0 errors.
- [x] 5.4 Run strict OpenSpec validation for this change and all specs.
  - Evidence: strict change validation passed; `validate --all --strict --no-interactive` passed 11 items.
- [x] 5.5 Run `git diff --check` and duplicate spec/archive-name check.
  - Evidence: `git diff --check` passed; duplicate spec/archive-name check reported `intersection_count=0` before archive.
- [x] 5.6 Perform self-review for scope, no-lookahead, threshold preservation, artifact completeness, and secret safety.
  - Review: implementation only adds three explicit research-only asymmetric ATR exit profile names; no entry filters, threshold changes, private data, live trading, push/MR/merge, or success notification were used. Quarterly artifact evidence falsifies the hypothesis (`best_realistic_passed_count=0/8`) rather than weakening criteria.
- [x] 5.7 Archive the completed change as success or falsified research evidence before commit.
  - Evidence: archived as `openspec/changes/archive/2026-06-27-compare-breakout-asymmetric-atr-exit-profiles` after strict validation; archive warning reflected these final closure checkboxes being completed after archive.
- [x] 5.8 Create one scoped local commit if repository state is safe.
  - Evidence: repository state is safe for a scoped commit with unrelated `.dev/autonomous_dev.sh` intentionally left unstaged; final report records the created commit hash.
