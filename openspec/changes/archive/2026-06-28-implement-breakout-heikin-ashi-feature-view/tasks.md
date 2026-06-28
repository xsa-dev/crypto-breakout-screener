## 1. Implementation
- [x] 1.1 Add causal Heikin-Ashi transform helper for OHLCV bars.
  - Evidence: `src/app/breakout/backtesting.py` computes deterministic derived HA feature snapshots from raw bars and records seed/source metadata.
- [x] 1.2 Add opt-in feature flags/settings for Heikin-Ashi feature view.
  - Evidence: `BacktestFeatureFilterConfig`, `BacktestConfirmationFilterConfig`, and `BacktestExitProfileConfig` expose disabled-by-default HA settings.
- [x] 1.3 Add named profile support for `heikin-ashi-trend-filter-v1`, `heikin-ashi-confirmation-v1`, and `heikin-ashi-exit-v1`.
  - Evidence: `src/app/breakout/experiments/crypto_batch.py` resolves all three named profiles.
- [x] 1.4 Export Heikin-Ashi body/wick/color/trend/compression/failure features in entry snapshots.
  - Evidence: enabled entry snapshots include HA body/wick ratios, close position, color/streak, trend persistence, compression, reversal, and failed-continuation hints.
- [x] 1.5 Allow setup scoring/diagnostics to consume Heikin-Ashi features without replacing raw OHLCV accounting.
  - Evidence: HA filters use feature snapshot fields only; exits still return raw bar closes/prices, and report parameter snapshots disclose raw OHLCV accounting.
- [x] 1.6 Add reporting fields that disclose Heikin-Ashi feature usage, active HA profile names, and raw-price accounting.
  - Evidence: batch JSON/CSV summaries include separate `heikin_ashi_*_profile` fields and `heikin_ashi_usage` disclosure.

## 2. Tests
- [x] 2.1 Test Heikin-Ashi transform is deterministic and causal.
  - Evidence: `test_heikin_ashi_feature_snapshot_is_opt_in_causal_and_derived_only` mutates future bars and verifies entry-time HA features are unchanged.
- [x] 2.2 Test transformed values are not used for fills, stops, PnL, costs, equity, or drawdown.
  - Evidence: `test_heikin_ashi_exit_uses_raw_close_and_discloses_raw_accounting` verifies HA exit uses raw close and raw accounting disclosure.
- [x] 2.3 Test feature snapshots include Heikin-Ashi fields only when enabled.
  - Evidence: `test_heikin_ashi_feature_snapshot_is_opt_in_causal_and_derived_only` verifies opt-in HA fields and default disabled behavior.
- [x] 2.4 Test score/reporting labels Heikin-Ashi as derived feature view.
  - Evidence: `test_batch_runner_records_heikin_ashi_named_profiles` verifies summary/CSV HA usage disclosure.
- [x] 2.5 Test density source remains `ohlcv_proxy` when no DOM/L2 exists.
  - Evidence: `test_batch_runner_records_heikin_ashi_named_profiles` verifies HA summary disclosure keeps density source as `ohlcv_proxy_or_unavailable`.
- [x] 2.6 Test the three named Heikin-Ashi profiles are selectable and reported separately from raw feature/confirmation/exit profiles.
  - Evidence: `test_batch_runner_records_heikin_ashi_named_profiles` covers all three named profiles and separate HA profile fields.

## 3. Verification
- [x] 3.1 Run targeted transform/setup/reporting tests.
  - Evidence: `uv run pytest tests/test_crypto_batch_experiment.py tests/test_breakout_backtesting_reporting.py -q` passed (87 tests).
- [x] 3.2 Run strict OpenSpec validation.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 validate implement-breakout-heikin-ashi-feature-view --strict --no-interactive` passed.
- [x] 3.3 Run `git diff --check`.
  - Evidence: `git diff --check` passed.
