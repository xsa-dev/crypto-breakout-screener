# Design

## Hypothesis

Favorable-timeout exits may reduce drawdown in the failed BTCUSDT quarters by closing accepted trades that do not prove continuation within the first few M15 bars. The rule is causal: after a fixed number of post-entry bars, if the highest high since entry has not reached the configured favorable ATR threshold, the trade exits at that bar close. If the favorable threshold has already been reached, the trade continues to the configured large target, close target, or fixed-hold fallback.

This is distinct from prior archived methods:

- unlike fixed holds, it conditionally shortens only stalled trades;
- unlike ATR stops or close stops, it does not wait for a fixed adverse threshold;
- unlike profit-lock trailing, it acts before a large favorable move and therefore targets stagnation/path-risk instead of profit giveback;
- unlike entry filters, it does not change trade creation or skip counts.

## Candidate profiles

1. `conservative-v1-m15-slope-positive-max-trades-8-target-3p0-fav-timeout-1p0-after-4-hold-32`
   - fixed holding: 32 M15 bars
   - intrabar target: +3.0 ATR
   - favorable-timeout threshold: +1.0 ATR
   - favorable-timeout check: after 4 M15 bars
2. `conservative-v1-m15-slope-positive-max-trades-8-target-4p0-fav-timeout-1p0-after-4-hold-32`
   - fixed holding: 32 M15 bars
   - intrabar target: +4.0 ATR
   - favorable-timeout threshold: +1.0 ATR
   - favorable-timeout check: after 4 M15 bars
3. `conservative-v1-m15-slope-positive-max-trades-8-close-target-2p0-fav-timeout-1p0-after-4-hold-32`
   - fixed holding: 32 M15 bars
   - close-confirmed target: +2.0 ATR
   - favorable-timeout threshold: +1.0 ATR
   - favorable-timeout check: after 4 M15 bars

These are fixed named profiles, not a parameter optimizer. If all fail `2024q1`, the slice is falsified and remaining quarters are recorded as blocked/not run after early falsification.

## Implementation plan

1. Extend `BacktestExitProfileConfig` with optional `favorable_timeout_atr` and `favorable_timeout_bars` fields, disabled by default.
2. Validate that the favorable-timeout pair is configured together and that the timeout bar is below `fixed_holding_bars`.
3. Add the three profile names to `EXIT_PROFILE_NAMES` and `exit_profile_config` in `src/app/breakout/experiments/crypto_batch.py`.
4. In `_resolve_exit`, track max favorable high from post-entry bars; at the configured timeout bar, exit at that bar close if the threshold has not been reached. Evaluate existing target/close-target/stop semantics first within the same bar so an intrabar target hit is not overwritten by the timeout.
5. Record favorable-timeout settings in trade metadata and batch `exit_profile_settings_json`.
6. Extend `tests/test_crypto_batch_experiment.py` for profile mapping/serialization and add a focused backtesting test proving stalled trades exit at timeout while default behavior remains unchanged.

## Verification commands

- `npx --yes @fission-ai/openspec@1.4.1 validate compare-breakout-favorable-timeout-exit-profiles --strict --no-interactive`
- `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`
- `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile tests/test_crypto_historical_experiment.py`
- `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_crypto_batch_experiment.py`
- `env UV_CACHE_DIR=.uv-cache uv run ruff check .`
- `env UV_CACHE_DIR=.uv-cache uv run pyright`
- `git diff --check`

Realistic early-falsification command pattern:

`env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.crypto_batch --windows 2024q1:2024-01-01T00:00:00Z/2024-04-01T00:00:00Z --gate-profile <profile> --reuse-market-data --market-data-dir artifacts/batch-market-data --output-dir artifacts/favorable-timeout-exit-profile-comparison/q1-smoke-<short-name> --spread 1.0 --slippage 0.5 --commission-rate 0.00055 --funding-rate-per-bar 0.00001`

Full promotion command pattern if a candidate passes the blocker quarter:

`env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.crypto_batch --preset quarterly-2023-2024 --gate-profile <profile> --reuse-market-data --market-data-dir artifacts/batch-market-data --output-dir artifacts/favorable-timeout-exit-profile-comparison/full-<short-name> --spread 1.0 --slippage 0.5 --commission-rate 0.00055 --funding-rate-per-bar 0.00001`

## Risks

Path-risk summaries show only modest favorable-before-adverse separation between passed and failed windows, so this may close profitable slow-developing trades along with bad stalled trades. If `2024q1` remains below thresholds or if full promotion regresses previously passed quarters, archive as falsified rather than expanding the slice with additional filters.
