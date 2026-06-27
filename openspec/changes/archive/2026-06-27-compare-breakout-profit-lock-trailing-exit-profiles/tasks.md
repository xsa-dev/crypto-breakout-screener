## 1. OpenSpec readiness
- [x] 1.1 Record unrelated dirty files and active OpenSpec changes before implementation.
  - Evidence: pre-implementation `git status --short` showed unrelated `M .dev/autonomous_dev.sh` and untracked active `openspec/changes/evaluate-breakout-altcoin-universe-profiles/`; these were left untouched and unstaged.
- [x] 1.2 Restore the BTCUSDT reference quarterly scorecard before source changes.
  - Evidence: proposal records `artifacts/realistic-cost-profile-search/conservative-v1-m15-slope-positive-max-trades-8/scorecard.csv` baseline rows: `5/8`, passes `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q3`, failures `2024q1`, `2024q2`, `2024q4`.
- [x] 1.3 Validate this change strictly before implementation.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 validate compare-breakout-profit-lock-trailing-exit-profiles --strict --no-interactive` passed; `validate --all --strict --no-interactive` passed with both active changes valid.

## 2. Implementation
- [x] 2.1 Add exactly the three fixed profit-lock trailing profile names.
  - Evidence: `src/app/breakout/experiments/crypto_batch.py` adds only the three named profit-lock trailing profiles to `EXIT_PROFILE_NAMES`.
- [x] 2.2 Map each profile to deterministic target/close-target plus trailing exit settings using existing post-entry M15 bars and entry-time ATR.
  - Evidence: `exit_profile_config()` maps target/close-target, trailing activation, trailing giveback, and fixed hold using existing `BacktestExitProfileConfig` fields; no new model fields or decision paths were added.
- [x] 2.3 Preserve default/reference behavior when no explicit profit-lock trailing profile is selected.
  - Evidence: implementation only adds disabled-by-default explicit names; existing baseline/reference profile branches and defaults are unchanged.

## 3. Tests
- [x] 3.1 Extend targeted batch-runner tests for profile mapping and summary serialization.
  - Evidence: `tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile` verifies profit-lock trailing summary serialization and close-target mapping.
- [x] 3.2 Run targeted pytest for exit-profile recording.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile` passed.

## 4. Quarterly experiment loop
- [x] 4.1 Run BTCUSDT `2024q1` early-falsification realistic-cost batches for all fixed candidates.
  - Evidence: all three candidates ran with cached public data, unchanged thresholds, and realistic costs (`spread=1.0`, `slippage=0.5`, `commission_rate=0.00055`, `funding_rate_per_bar=0.00001`).
- [x] 4.2 Promote any candidate that passes `2024q1` to the full `2023q1..2024q4` scorecard.
  - Evidence: no candidate passed `2024q1`; full scorecard promotion was not applicable.
- [x] 4.3 Produce/record updated quarterly scorecard artifact paths, blockers, metrics, and status changes versus the 5/8 reference.
  - Evidence: combined artifacts written to `artifacts/profit-lock-trailing-exit-profile-comparison/early-falsified/summary.json` and `artifacts/profit-lock-trailing-exit-profile-comparison/early-falsified/scorecard.csv`.
  - Result: no quarter improved to pass. `2024q1` remains failed for all candidates on `max_drawdown_below_threshold`: target-3p0 trail (`net_profit=175666.03`, `profit_factor=1.6117`, `max_drawdown=-0.5172`), target-4p0 trail (`net_profit=242582.29`, `profit_factor=1.8010`, `max_drawdown=-0.5493`), close-target trail (`net_profit=187047.49`, `profit_factor=1.6569`, `max_drawdown=-0.5066`).
- [x] 4.4 If no candidate reaches `8/8`, mark the hypothesis falsified and do not send success notification.
  - Verdict: falsified/negative evidence. All candidates are early-falsified by required window `2024q1`; no success notification sent.

## 5. Verification and closure
- [x] 5.1 Run relevant pytest.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile` passed; `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_crypto_batch_experiment.py` passed.
- [x] 5.2 Run `uv run ruff check .`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run ruff check .` passed.
- [x] 5.3 Run `uv run pyright`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pyright` passed.
- [x] 5.4 Run strict OpenSpec validation for this change and all specs.
  - Evidence: final strict change validation and `validate --all --strict --no-interactive` passed before archive.
- [x] 5.5 Run `git diff --check` and duplicate spec/archive-name check.
  - Evidence: `git diff --check` passed; duplicate active-spec/archive-name check reported zero intersections.
- [x] 5.6 Perform self-review against acceptance criteria, thresholds, safety, and scope.
  - Review: diff only adds disabled-by-default named BTCUSDT research profiles and targeted tests; thresholds, costs, entry filters, BTCUSDT data scope, private/live API prohibition, and default behavior remain unchanged. Real quarterly evidence falsified the hypothesis below `8/8`.
- [x] 5.7 Archive as success only on realistic-cost `8/8`; otherwise archive as falsified/negative research evidence.
  - Evidence: archived as falsified negative evidence after final validation.
- [x] 5.8 Create one scoped local commit if repository state is safe.
  - Evidence: local commit created for this change only; unrelated `.dev/autonomous_dev.sh` and active altcoin-universe change were left unstaged.
