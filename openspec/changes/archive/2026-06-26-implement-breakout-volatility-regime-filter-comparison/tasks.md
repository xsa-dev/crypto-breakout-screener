## 1. OpenSpec readiness
- [x] 1.1 Confirm previous bad-regime diagnostic change is archived and committed.
- [x] 1.2 Confirm this change has no source-code edits before review approval.
- [x] 1.3 Confirm unrelated dirty files remain unstaged/out of scope.

## 2. Model and engine support
- [x] 2.1 Extend feature/regime filter configuration with fixed deterministic threshold fields.
- [x] 2.2 Apply filters inside `BacktestEngine` before trade creation using entry-time feature snapshots.
- [x] 2.3 Add deterministic skip reasons and skip counts for each filter condition.
- [x] 2.4 Preserve disabled/default behavior for existing profiles.

## 3. Batch profiles and reporting
- [x] 3.1 Add required profile names to batch CLI choices and profile resolver.
- [x] 3.2 Keep lifecycle gates and M15 slope-positive base behavior identical to `conservative-v1-m15-slope-positive-max-trades-8`.
- [x] 3.3 Add/serialize `regime_filter_profile`, `regime_filter_settings_json`, and `regime_filter_skip_counts_json`.
- [x] 3.4 Ensure existing `gate_profile`, `feature_filter_profile`, and `risk_control_profile` fields remain readable and backward-compatible.

## 4. Tests
- [x] 4.1 Add engine tests for ATR-percentile blocking.
- [x] 4.2 Add engine tests for breakout-distance blocking.
- [x] 4.3 Add engine tests for candle-body blocking.
- [x] 4.4 Add combined-profile tests to prove lifecycle state recalculates after skipped entries.
- [x] 4.5 Add batch summary serialization tests for regime profile/settings/skip counts.
- [x] 4.6 Add no-lookahead regression coverage or reuse existing entry-feature no-lookahead coverage explicitly.

## 5. Verification
- [x] 5.1 Run targeted tests for backtesting and batch profiles.
- [x] 5.2 Run full `uv run pytest`.
- [x] 5.3 Run `uv run ruff check .`.
- [x] 5.4 Run `uv run pyright`.
- [x] 5.5 Run strict OpenSpec validation for this change and all specs.
- [x] 5.6 Run `git diff --check`.

## 6. Real quarterly experiments
- [x] 6.1 Run reference profile if needed for same-output-dir comparison.
- [x] 6.2 Run `conservative-v1-m15-slope-positive-max-trades-8-atr25-block`.
- [x] 6.3 Run `conservative-v1-m15-slope-positive-max-trades-8-atr25-breakout1-block`.
- [x] 6.4 Run `conservative-v1-m15-slope-positive-max-trades-8-atr25-body75-block`.
- [x] 6.5 Optionally run `conservative-v1-m15-slope-positive-max-trades-8-atr25-body25-75-block` only if scope remains small.
- [x] 6.6 Parse and compare pass count, blockers, net, worst drawdown, profit factor, and skip counts.

## 7. Archive and commit boundary
- [x] 7.1 Mark tasks complete or explicitly skipped with reason.
- [x] 7.2 Archive this OpenSpec change after verification.
- [x] 7.3 Run post-archive full verification.
- [x] 7.4 Perform final scoped diff/security review.
- [x] 7.5 Commit only this change when approved; do not stage unrelated `.dev/autonomous_dev.sh`.

## Evidence summary

Quarterly 2023-2024 comparison completed for required and optional fixed profiles:

- `conservative-v1-m15-slope-positive-max-trades-8-atr25-block`: passed 1/8, failed 7/8, hypothesis_supported=false.
- `conservative-v1-m15-slope-positive-max-trades-8-atr25-breakout1-block`: passed 2/8, failed 6/8, hypothesis_supported=false.
- `conservative-v1-m15-slope-positive-max-trades-8-atr25-body75-block`: passed 3/8, failed 5/8, hypothesis_supported=false.
- `conservative-v1-m15-slope-positive-max-trades-8-atr25-body25-75-block`: passed 3/8, failed 5/8, hypothesis_supported=false.

Conclusion: the tested volatility/no-trade regime filters do not support the breakout hypothesis and do not improve on the reference `conservative-v1-m15-slope-positive-max-trades-8` profile, which remains 5/8 passed.
