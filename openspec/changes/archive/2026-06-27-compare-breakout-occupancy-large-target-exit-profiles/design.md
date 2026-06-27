# Design

## Hypothesis
The primary shared blocker remains path-risk/drawdown in `2024q1` with secondary failures in `2024q2` and `2024q4`. Existing evidence suggests two facts can coexist:

1. Large-target exits (`target-4p0-hold-32`, `close-target-2p0-hold-32`) can improve `2024q1` net profit and profit factor versus the reference.
2. Without honest one-active-position occupancy, overlapping synthetic holds can create excessive concurrent path exposure and realized drawdown.

The hypothesis is that combining the strongest observed large-target exit family with existing occupancy gating can keep enough gross edge while reducing turnover/overlap-driven drawdown enough to move the scorecard toward `8/8`.

## Fixed candidate set

1. `conservative-v1-m15-slope-positive-max-trades-8-occupancy-target-4p0-hold-32`
   - `block_overlapping_positions=true`
   - fixed holding: 32 M15 bars
   - intrabar target: +4.0 ATR
2. `conservative-v1-m15-slope-positive-max-trades-8-occupancy-close-target-2p0-hold-32`
   - `block_overlapping_positions=true`
   - fixed holding: 32 M15 bars
   - close-confirmed target: +2.0 ATR

These are fixed named profiles, not a parameter optimizer. If both fail `2024q1`, remaining quarters are blocked/not run after early falsification and the change is archived as falsified.

## Implementation plan

1. Add the two names to `EXIT_PROFILE_NAMES` in `src/app/breakout/experiments/crypto_batch.py`.
2. Reuse the existing `research_gate_profile` substring rule (`-occupancy-`) to set `block_overlapping_positions=true`.
3. Map the two names in `exit_profile_config` to existing `BacktestExitProfileConfig` values.
4. Extend `tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile` or nearby tests to verify the mappings and serialized settings.
5. Run realistic-cost `2024q1` batches for both candidates; promote only a pass to full quarterly scorecard.

## Verification commands

- `npx --yes @fission-ai/openspec@1.4.1 validate compare-breakout-occupancy-large-target-exit-profiles --strict --no-interactive`
- `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`
- `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile`
- `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_crypto_batch_experiment.py`
- `env UV_CACHE_DIR=.uv-cache uv run ruff check .`
- `env UV_CACHE_DIR=.uv-cache uv run pyright`
- `git diff --check`

Early-falsification command pattern:

`env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.crypto_batch --windows 2024q1:2024-01-01T00:00:00Z/2024-04-01T00:00:00Z --gate-profile <profile> --reuse-market-data --market-data-dir artifacts/batch-market-data --output-dir artifacts/occupancy-large-target-exit-profile-comparison/q1-smoke-<short-name> --spread 1.0 --slippage 0.5 --commission-rate 0.00055 --funding-rate-per-bar 0.00001`

Full promotion command pattern if a candidate passes `2024q1`:

`env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.crypto_batch --preset quarterly-2023-2024 --gate-profile <profile> --reuse-market-data --market-data-dir artifacts/batch-market-data --output-dir artifacts/occupancy-large-target-exit-profile-comparison/full-<short-name> --spread 1.0 --slippage 0.5 --commission-rate 0.00055 --funding-rate-per-bar 0.00001`

## Risks
Occupancy may reduce trade count and net profit too much, especially in `2024q2`, while still leaving large drawdown from the trades it does take. If `2024q1` remains below thresholds, do not expand this change into new filters or alternate parameters; record negative evidence and archive.
