## 1. Requirements and baseline evidence
- [x] 1.1 Restore the reference quarterly scorecard for `conservative-v1-m15-slope-positive-max-trades-8` before source implementation.
- [x] 1.2 Confirm unchanged research thresholds: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, `require_no_feed_gaps=true`.
- [x] 1.3 Confirm this change targets a distinct delayed close-stop path-risk mechanism and does not repeat archived immediate stop/trailing/partial/large-target methods as-is.

## 2. Implementation
- [x] 2.1 Add disabled-by-default delayed close-stop configuration.
- [x] 2.2 Implement delayed close-stop evaluation without changing default/legacy close-stop behavior.
- [x] 2.3 Add fixed named delayed close-stop profile names to the batch runner.
- [x] 2.4 Serialize delayed close-stop settings in deterministic batch summaries and trade metadata.

## 3. Tests
- [x] 3.1 Test delayed close-stop waits through the configured grace bars and then exits on close breach.
- [x] 3.2 Test default immediate close-stop behavior remains unchanged.
- [x] 3.3 Test invalid delayed close-stop config is rejected when no close-stop threshold exists.
- [x] 3.4 Test named profiles resolve to expected settings and batch summaries record them.

## 4. Real research run
- [x] 4.1 Run BTCUSDT realistic-cost evidence for fixed delayed close-stop profiles; all three candidates early-falsified on required quarter `2024q1`.
- [x] 4.2 Produce/record updated quarterly scorecard and artifact paths: `artifacts/delayed-close-stop-exit-profile-comparison/early-falsified/summary.json` and `scorecard.csv`.
- [x] 4.3 State which quarters changed status versus the 5/8 reference: `2024q1` improved net/PF to pass for all candidates, but max drawdown remained failed, so the score did not reach `8/8`.
- [x] 4.4 Result is below `8/8`; delayed close-stop is falsified by `2024q1:max_drawdown_below_threshold` and remaining quarters are blocked/not run after early falsification.

## 5. Verification and archive
- [x] 5.1 Run strict OpenSpec validation for this change and all specs.
- [x] 5.2 Run relevant pytest/ruff/pyright/build checks or document exact blockers.
- [x] 5.3 Run self-review against OpenSpec criteria and secret/live-safety constraints.
- [x] 5.4 Archive the checked research change as successful only for `8/8`, otherwise as falsified negative evidence.
- [x] 5.5 Create one scoped local commit if the working tree can be safely staged without unrelated changes.
