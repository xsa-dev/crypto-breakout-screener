## 1. Requirements and baseline evidence
- [x] 1.1 Restore the reference quarterly scorecard for `conservative-v1-m15-slope-positive-max-trades-8` before source implementation.
- [x] 1.2 Confirm unchanged research thresholds: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, `require_no_feed_gaps=true`.
- [x] 1.3 Confirm this change targets a distinct exposure/path-risk mechanism and does not repeat archived stop/trailing/partial/large-target methods as-is.

## 2. Implementation
- [x] 2.1 Add fixed exposure-scaled large-target profile names.
- [x] 2.2 Forward `base_quantity=0.5` only for the explicit `*-qty-0p5` profiles while preserving the default batch quantity.
- [x] 2.3 Serialize exposure settings in deterministic batch summary JSON/CSV and batch ids.
- [x] 2.4 Preserve baseline/reference behavior when no exposure-scaled profile is selected.

## 3. Tests
- [x] 3.1 Test the three fixed profile names map to expected exit and exposure settings.
- [x] 3.2 Test batch execution forwards and records `base_quantity=0.5` for `*-qty-0p5` profiles.
- [x] 3.3 Test default profiles keep the existing default `base_quantity=10.0` behavior.
- [x] 3.4 Test summary CSV/JSON records exposure settings separately from exit/cost settings.

## 4. Real research run
- [x] 4.1 Run BTCUSDT realistic-cost early-falsification batches for all fixed profiles with unchanged thresholds; all failed required quarter `2024q2`.
- [x] 4.2 Produce/record updated quarterly scorecard and artifact paths: `artifacts/scaled-exit-exposure-profile-comparison/early-falsified/summary.json` and `scorecard.csv`.
- [x] 4.3 State which quarters changed status versus the 5/8 reference: `2024q1` exploratory checks improved to pass for the fixed profiles, but `2024q2` remains failed for all candidates, so the score did not reach `8/8`.
- [x] 4.4 If the result is below `8/8`, record the falsified verdict and remaining blockers.

## 5. Verification and archive
- [x] 5.1 Run strict OpenSpec validation for this change and all specs.
- [x] 5.2 Run relevant pytest/ruff/pyright/build checks or document exact blockers.
- [x] 5.3 Run self-review against the OpenSpec criteria and secret/live-safety constraints.
- [x] 5.4 Archive the checked research change as falsified negative evidence.
- [x] 5.5 Create one scoped local commit if the working tree can be safely staged without unrelated changes.
