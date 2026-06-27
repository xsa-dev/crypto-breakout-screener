## 1. OpenSpec readiness
- [x] 1.1 Record active/unrelated dirty files and confirm this change is the selected BTCUSDT owner-goal work. Evidence: unrelated pre-existing `.dev/autonomous_dev.sh` modification and `openspec/changes/evaluate-breakout-altcoin-universe-profiles/` untracked active change were left untouched; this change targets the owner-goal BTCUSDT path-risk/exit line.
- [x] 1.2 Record the pre-change quarterly scorecard, failing quarters, thresholds, artifact path, and verification command. Evidence: proposal records `artifacts/realistic-cost-profile-search/conservative-v1-m15-slope-positive-max-trades-8/scorecard.csv`, reference `5/8`, failing `2024q1`, `2024q2`, `2024q4`, and thresholds `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, `require_no_feed_gaps=true`.
- [x] 1.3 Validate this change strictly before source implementation. Evidence: `npx --yes @fission-ai/openspec@1.4.1 validate compare-breakout-favorable-timeout-exit-profiles --strict --no-interactive` passed before source edits.

## 2. Implementation
- [x] 2.1 Add disabled-by-default favorable-timeout exit settings to the backtest config model. Evidence: `BacktestExitProfileConfig` has optional `favorable_timeout_atr` and `favorable_timeout_bars` with pair/range validation.
- [x] 2.2 Implement causal post-entry favorable-timeout exit resolution without changing default behavior. Evidence: `_resolve_exit` exits at timeout close only when the configured favorable ATR threshold was not reached by the timeout bar; default profile remains unchanged.
- [x] 2.3 Add fixed named favorable-timeout profiles to the batch runner. Evidence: three `conservative-v1-m15-slope-positive-max-trades-8-...fav-timeout...` profile names map to deterministic settings.
- [x] 2.4 Record favorable-timeout settings in exit profile settings and trade metadata. Evidence: batch `exit_profile_settings_json` and trade metadata include `favorable_timeout_atr` and `favorable_timeout_bars` fields.

## 3. Tests
- [x] 3.1 Add/extend tests that named favorable-timeout profiles serialize deterministic settings. Evidence: `tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile` covers the target and close-target favorable-timeout profiles.
- [x] 3.2 Add a focused backtesting test for stalled-trade timeout exit behavior. Evidence: `tests/test_breakout_backtesting_reporting.py::test_favorable_timeout_exit_closes_stalled_trade_and_records_metadata` verifies `favorable_timeout_exit` and metadata.
- [x] 3.3 Add/confirm tests that default exit behavior remains unchanged. Evidence: full `uv run pytest` passed 125 tests including existing deterministic/default backtest tests.

## 4. Quarterly experiment loop
- [x] 4.1 Run realistic-cost `2024q1` early-falsification for each candidate. Evidence: ran all three candidates with `--spread 1.0 --slippage 0.5 --commission-rate 0.00055 --funding-rate-per-bar 0.00001` and cached public data.
- [x] 4.2 Promote any candidate that passes `2024q1` to full `2023q1..2024q4` quarterly scorecard. Evidence: no candidate passed `2024q1`; full promotion was not justified.
- [x] 4.3 Record per-quarter pass/fail/blocked status, blockers, metrics, and artifact paths. Evidence: `target-3p0...` `2024q1` net `1657.09`, PF `1.0047`, max DD `-2.7121`, blocker `max_drawdown_below_threshold`, artifact `artifacts/favorable-timeout-exit-profile-comparison/q1-smoke-target-3p0-fav-timeout-1p0-after-4-hold-32/crypto/BTCUSDT/01981b9e7e2611a3/summary.json`; `target-4p0...` net `10861.95`, PF `1.0290`, max DD `-2.4154`, blocker `max_drawdown_below_threshold`, artifact `artifacts/favorable-timeout-exit-profile-comparison/q1-smoke-target-4p0-fav-timeout-1p0-after-4-hold-32/crypto/BTCUSDT/41689c60e25a3ae9/summary.json`; `close-target-2p0...` net `-41081.03`, PF `0.8873`, max DD `-4.0993`, blockers `net_profit_below_threshold;profit_factor_below_threshold;max_drawdown_below_threshold`, artifact `artifacts/favorable-timeout-exit-profile-comparison/q1-smoke-close-target-2p0-fav-timeout-1p0-after-4-hold-32/crypto/BTCUSDT/953fdd38c059f3eb/summary.json`.
- [x] 4.4 State whether the score moved from the reference `5/8` toward `8/8`. Evidence: no movement toward `8/8`; all candidates failed the primary `2024q1` blocker quarter under required realistic costs, so the hypothesis is falsified/negative evidence.

## 5. Verification and closure
- [x] 5.1 Run targeted pytest. Evidence: targeted pytest for exit-profile mapping and favorable-timeout tests passed (`3 passed`).
- [x] 5.2 Run full relevant pytest if source behavior changed broadly. Evidence: `env UV_CACHE_DIR=.uv-cache uv run pytest` passed `125 passed`.
- [x] 5.3 Run `uv run ruff check .`. Evidence: `env UV_CACHE_DIR=.uv-cache uv run ruff check .` passed.
- [x] 5.4 Run `uv run pyright`. Evidence: `env UV_CACHE_DIR=.uv-cache uv run pyright` passed with `0 errors, 0 warnings`.
- [x] 5.5 Run strict OpenSpec validation for this change and all specs. Evidence: change validation and `validate --all --strict --no-interactive` passed with 12 items.
- [x] 5.6 Run `git diff --check` and duplicate spec/archive-name check. Evidence: `git diff --check` passed; duplicate spec/archive-name check is run after archive.
- [x] 5.7 Archive as success only if one candidate reaches required `8/8`; otherwise archive as falsified/negative research evidence. Evidence: all candidates failed `2024q1`; archive as falsified/negative research evidence.
- [x] 5.8 Create one scoped local commit if repository state is safe. Evidence: commit is created after archive and post-archive validation, excluding unrelated `.dev/autonomous_dev.sh` and unrelated `evaluate-breakout-altcoin-universe-profiles` files.
