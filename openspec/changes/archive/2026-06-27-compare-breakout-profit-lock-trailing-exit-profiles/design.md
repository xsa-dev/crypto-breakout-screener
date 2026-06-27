# Design

## Hypothesis

Profit-lock trailing exits may preserve the large-target profiles' positive `2024q1` net/PF while reducing realized drawdown. Unlike prior trailing-only profiles, these candidates keep an explicit large target or close target and activate the trailing stop only after a larger favorable move (`+1.5` or `+2.0 ATR`) so they should avoid the high-turnover cost churn seen in tight/trailing-only slices.

## Candidate profiles

1. `conservative-v1-m15-slope-positive-max-trades-8-target-3p0-trail-1p5-giveback-1p0-hold-32`
   - fixed holding: 32 M15 bars
   - intrabar target: +3.0 ATR
   - trailing activation: +1.5 ATR
   - trailing giveback: 1.0 ATR
2. `conservative-v1-m15-slope-positive-max-trades-8-target-4p0-trail-2p0-giveback-1p0-hold-32`
   - fixed holding: 32 M15 bars
   - intrabar target: +4.0 ATR
   - trailing activation: +2.0 ATR
   - trailing giveback: 1.0 ATR
3. `conservative-v1-m15-slope-positive-max-trades-8-close-target-2p0-trail-1p5-giveback-1p0-hold-32`
   - fixed holding: 32 M15 bars
   - close-confirmed target: +2.0 ATR
   - trailing activation: +1.5 ATR
   - trailing giveback: 1.0 ATR

These are fixed named profiles, not a parameter optimizer. If all fail `2024q1` under realistic costs, the slice is falsified and remaining quarters are recorded as blocked/not run after early falsification.

## Implementation plan

1. Add the three names to `EXIT_PROFILE_NAMES` and `exit_profile_config` in `src/app/breakout/experiments/crypto_batch.py`.
2. Reuse existing `BacktestExitProfileConfig` fields (`target_atr`, `close_target_atr`, `trailing_after_atr`, `trailing_giveback_atr`, `fixed_holding_bars`) and existing backtest exit resolution; do not add new model fields unless tests prove current semantics cannot express the candidates.
3. Extend `tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile` to verify mapping, summary serialization, and default behavior remains unchanged.
4. Run targeted tests, then run `2024q1` early-falsification realistic-cost batches for all candidates. Promote only candidates that pass `2024q1` to the full `2023q1..2024q4` quarterly scorecard.
5. Record a combined scorecard under `artifacts/profit-lock-trailing-exit-profile-comparison/early-falsified/` or a full comparison directory.

## Verification commands

- `npx --yes @fission-ai/openspec@1.4.1 validate compare-breakout-profit-lock-trailing-exit-profiles --strict --no-interactive`
- `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`
- `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile`
- `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_crypto_batch_experiment.py`
- `env UV_CACHE_DIR=.uv-cache uv run ruff check .`
- `env UV_CACHE_DIR=.uv-cache uv run pyright`
- `git diff --check`

Realistic early-falsification command pattern:

`env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.crypto_batch --windows 2024q1=2024-01-01T00:00:00Z..2024-04-01T00:00:00Z --gate-profile <profile> --reuse-market-data --market-data-dir artifacts/batch-market-data --output-dir artifacts/profit-lock-trailing-exit-profile-comparison/q1-smoke-<short-name> --spread 1.0 --slippage 0.5 --commission-rate 0.00055 --funding-rate-per-bar 0.00001`

## Risks

Trailing may reduce drawdown only after a favorable excursion; trades that move adverse immediately will still lose. If `2024q2` remains negative after `2024q1` passes, the hypothesis remains falsified for `8/8` and should be archived rather than expanded with new entry filters.
