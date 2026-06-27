## 1. OpenSpec readiness
- [x] 1.1 Confirm no active OpenSpec changes and record unrelated dirty files.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 list` showed no active changes; `git status --short --branch` showed unrelated modified `.dev/autonomous_dev.sh` before this change.
- [x] 1.2 Reconstruct the current reference scorecard and failing windows before implementation.
  - Evidence: design records `conservative-v1-m15-slope-positive-max-trades-8` as `5/8` with failed quarters `2024q1`, `2024q2`, `2024q4` from `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/2396740c76d50b91/summary.json`.
- [x] 1.3 Validate this change strictly before source implementation.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 validate compare-breakout-extended-hold-exit-profiles --strict --no-interactive` and `validate --all --strict --no-interactive` passed.

## 2. Implementation
- [x] 2.1 Add fixed named extended-hold exit profiles for hold 8, 16, and 32 bars.
  - Evidence: `EXIT_PROFILE_NAMES` and `exit_profile_config` now include `hold-8`, `hold-16`, and `hold-32`.
- [x] 2.2 Preserve default/reference exit behavior and all non-exit profile settings.
  - Evidence: new profiles are selected only by explicit gate-profile names; default/reference profile names still resolve to the existing settings.
- [x] 2.3 Ensure exit profile settings/counts serialize in existing batch JSON/CSV outputs.
  - Evidence: `test_batch_runner_records_exit_profile` asserts named exit settings serialization; real summaries under `artifacts/extended-hold-exit-profile-comparison/.../summary.json` record exit profile fields.

## 3. Tests
- [x] 3.1 Add or update batch/profile tests for the new named profile resolution.
  - Evidence: `tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile` asserts `hold-32` resolves to `fixed_holding_bars=32`.
- [x] 3.2 Run targeted tests covering exit profile settings and realistic-cost classification.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile` passed; final targeted suite recorded below.

## 4. Quarterly experiment loop
- [x] 4.1 Run each fixed candidate over `2023q1..2024q4` with cached public data.
  - Evidence: real quarterly batch summaries:
    - `hold-8`: `artifacts/extended-hold-exit-profile-comparison/conservative-v1-m15-slope-positive-max-trades-8-hold-8/crypto/BTCUSDT/0c7bfa2a4991fcc9/summary.json`
    - `hold-16`: `artifacts/extended-hold-exit-profile-comparison/conservative-v1-m15-slope-positive-max-trades-8-hold-16/crypto/BTCUSDT/4ce428bae3f85c85/summary.json`
    - `hold-32`: `artifacts/extended-hold-exit-profile-comparison/conservative-v1-m15-slope-positive-max-trades-8-hold-32/crypto/BTCUSDT/93d4ce8d619dca32/summary.json`
- [x] 4.2 Record baseline pass/fail scorecard for each candidate.
  - Evidence:
    - `hold-8`: baseline `3/8`; passed `2023q3`, `2023q4`, `2024q1`; failed `2023q1`, `2023q2`, `2024q2`, `2024q3`, `2024q4` on drawdown.
    - `hold-16`: baseline `1/8`; passed `2023q4`; failed all other quarters on drawdown.
    - `hold-32`: baseline `1/8`; passed `2024q1`; failed all other quarters on drawdown.
- [x] 4.3 Run realistic-cost robustness summary with `commission_rate=0.00055`, stressed spread/slippage, and positive funding.
  - Evidence: `artifacts/extended-hold-exit-profile-comparison-summary/realistic-cost/summary.json` and `scorecard.csv`; realistic settings include `spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055`, `funding_rate_per_bar=0.00001`.
- [x] 4.4 Update tasks with per-quarter status changes, blockers, metrics, and artifact paths.
  - Evidence: this task list records baseline changes; realistic scorecard records all per-quarter blockers.
  - Realistic scores: `hold-8` `0/8`; `hold-16` `0/8`; `hold-32` `1/8` with only `2024q1` passing and all other quarters blocked mainly by drawdown, plus net/PF misses in `2023q2` and `2023q3`.
- [x] 4.5 If no candidate reaches realistic-cost `8/8`, mark the hypothesis falsified and do not send success notification.
  - Verdict: falsified. Best realistic-cost score was `1/8`; no `net_costs_supported_candidates`; no success notification sent.

## 5. Verification and closure
- [x] 5.1 Run targeted and full pytest as appropriate.
  - Evidence: targeted `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_crypto_batch_experiment.py tests/test_realistic_cost_profile_search.py` passed 17 tests; full `env UV_CACHE_DIR=.uv-cache uv run pytest` passed 106 tests.
- [x] 5.2 Run `uv run ruff check .`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run ruff check .` passed.
- [x] 5.3 Run `uv run pyright`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pyright` passed with 0 errors.
- [x] 5.4 Run strict OpenSpec validation for this change and all specs.
  - Evidence: strict change validation passed; `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive` passed 11 items before archive.
- [x] 5.5 Run `git diff --check` and duplicate spec/archive-name check.
  - Evidence: `git diff --check` passed before archive; duplicate spec/archive-name check to be repeated after archive.
- [x] 5.6 Perform self-review for scope, no-lookahead, threshold preservation, artifact completeness, and secret safety.
  - Review: implementation only adds explicit research-only fixed holding profile names plus the validation bound needed for the pre-specified 32-bar candidate; no entry filters, thresholds, private data, live trading, push/MR/merge, or success notification were used. Quarterly artifact evidence falsifies the hypothesis (`best_realistic_passed_count=1/8`) rather than weakening criteria.
- [x] 5.7 Archive the completed change as success or falsified research evidence before commit.
  - Evidence: closure proceeds to archive this completed falsified research change after final validation; archived path and post-archive validation are recorded in the final report.
- [x] 5.8 Create one scoped local commit if repository state is safe.
  - Evidence: repository is safe for a scoped commit with unrelated `.dev/autonomous_dev.sh` intentionally left unstaged; final report records the commit hash.
