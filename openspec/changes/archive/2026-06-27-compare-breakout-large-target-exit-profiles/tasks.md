## 1. OpenSpec readiness
- [x] 1.1 Confirm no active OpenSpec changes and record unrelated dirty files.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 list` showed no active changes; `git status --short --branch` showed unrelated modified `.dev/autonomous_dev.sh` before this change.
- [x] 1.2 Reconstruct the current reference scorecard and failing windows before implementation.
  - Evidence: proposal records `conservative-v1-m15-slope-positive-max-trades-8` as `5/8` with failed quarters `2024q1`, `2024q2`, `2024q4` from `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/2396740c76d50b91/summary.json`.
- [x] 1.3 Validate this change strictly before source implementation.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 validate compare-breakout-large-target-exit-profiles --strict --no-interactive` and `validate --all --strict --no-interactive` passed.

## 2. Implementation
- [x] 2.1 Add exactly the three fixed named large-target exit profiles.
  - Evidence: `EXIT_PROFILE_NAMES` and `exit_profile_config` include `target-3p0-hold-32`, `target-4p0-hold-32`, and `close-target-2p0-hold-32`.
- [x] 2.2 Preserve default/reference behavior and all non-exit profile settings.
  - Evidence: profiles are selected only by explicit names and reuse existing reference gates, M15 slope feature filter, and max-trades risk control.
- [x] 2.3 Ensure large-target exit profile settings serialize in existing batch JSON/CSV outputs.
  - Evidence: `tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile` asserts the new fixed settings; real batch summaries record `exit_profile_settings` and `exit_profile_counts`.

## 3. Tests
- [x] 3.1 Add or update batch/profile tests for the new named profile resolution and serialization.
  - Evidence: `test_batch_runner_records_exit_profile` covers all three new names and expected settings.
- [x] 3.2 Run targeted tests covering large-target profile settings and realistic-cost classification.
  - Evidence: targeted pytest for `test_batch_runner_records_exit_profile` passed; targeted ruff over edited Python files passed.

## 4. Quarterly experiment loop
- [x] 4.1 Run each fixed candidate with cached public data until a required realistic-cost quarter falsifies the candidate or all eight quarters pass.
  - Evidence: exact cached-data realistic-cost runs evaluated `2024q1` for all three candidates; each failed `2024q1` on `max_drawdown_below_threshold`, so none can reach required `8/8`.
- [x] 4.2 Record baseline pass/fail evidence for each candidate where run before early falsification.
  - Evidence: baseline scorecards were not run after realistic `2024q1` early falsification because success requires realistic-cost `8/8`; remaining required windows are marked blocked/not run in the scorecard.
- [x] 4.3 Run realistic-cost checks with `spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055`, and `funding_rate_per_bar=0.00001`.
  - Evidence: realistic summaries under `artifacts/large-target-exit-profile-comparison-realistic-smoke/.../summary.json`; combined early-falsified summary at `artifacts/large-target-exit-profile-comparison-summary/early-falsified/summary.json`.
- [x] 4.4 Update tasks with per-quarter status changes, blockers, metrics, and artifact paths.
  - Evidence: `artifacts/large-target-exit-profile-comparison-summary/early-falsified/scorecard.csv` records required windows; `2024q1` is failed for every candidate and remaining quarters are marked blocked/not run after early falsification.
- [x] 4.5 If no candidate reaches realistic-cost `8/8`, mark the hypothesis falsified and do not send success notification.
  - Verdict: falsified. `target-3p0-hold-32` realistic `2024q1` failed drawdown (`net_profit=257132.13`, `profit_factor=1.8027`, `max_drawdown=-0.7416`); `target-4p0-hold-32` failed drawdown (`net_profit=340063.67`, `profit_factor=2.0268`, `max_drawdown=-0.6480`); `close-target-2p0-hold-32` failed drawdown (`net_profit=240929.11`, `profit_factor=1.7858`, `max_drawdown=-0.7135`). No success notification sent.

## 5. Verification and closure
- [x] 5.1 Run targeted and full pytest as appropriate.
  - Evidence: targeted pytest passed 1 test; final `env UV_CACHE_DIR=.uv-cache uv run pytest` passed 117 tests.
- [x] 5.2 Run `uv run ruff check .`.
  - Evidence: targeted ruff over edited Python files passed; final `env UV_CACHE_DIR=.uv-cache uv run ruff check .` passed.
- [x] 5.3 Run `uv run pyright`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pyright` passed with 0 errors.
- [x] 5.4 Run strict OpenSpec validation for this change and all specs.
  - Evidence: strict change validation passed; `validate --all --strict --no-interactive` passed 11 items.
- [x] 5.5 Run `git diff --check` and duplicate spec/archive-name check.
  - Evidence: `git diff --check` passed; duplicate spec/archive-name check reported `intersection_count=0` before archive.
- [x] 5.6 Perform self-review for scope, no-lookahead, threshold preservation, artifact completeness, and secret safety.
  - Review: implementation adds only three explicit target-only research profiles that reuse existing target/fixed-hold logic; default/reference behavior remains disabled-by-default; no entry filters, thresholds, private data, live trading, push/MR/merge, or success notification were used. Realistic-cost `2024q1` falsifies all candidates on drawdown, so the score did not reach `8/8`.
- [x] 5.7 Archive the completed change as success or falsified research evidence before commit.
  - Evidence: archived as `openspec/changes/archive/2026-06-27-compare-breakout-large-target-exit-profiles`; the archive warning reflected these final closure checkboxes being completed after archive.
- [x] 5.8 Create one scoped local commit if repository state is safe.
  - Evidence: repository is safe for a scoped commit with unrelated `.dev/autonomous_dev.sh` intentionally left unstaged; final report records the commit hash.
