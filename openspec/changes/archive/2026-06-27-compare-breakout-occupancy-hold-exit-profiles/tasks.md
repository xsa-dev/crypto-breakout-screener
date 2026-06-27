## 1. Requirements and baseline evidence
- [x] 1.1 Restore the reference quarterly scorecard for `conservative-v1-m15-slope-positive-max-trades-8` before source implementation.
- [x] 1.2 Confirm unchanged research thresholds: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, `require_no_feed_gaps=true`.
- [x] 1.3 Confirm this change targets the shared path/holding/occupancy mechanism and does not repeat archived stop/trailing/partial/large-target methods as-is.

## 2. Implementation
- [x] 2.1 Add a disabled-by-default one-position occupancy research gate.
- [x] 2.2 Add fixed occupancy-aware holding/target profile names and settings.
- [x] 2.3 Ensure batch summaries serialize occupancy gate settings and skip counts separately through existing gate/risk fields.
- [x] 2.4 Preserve baseline/reference behavior when occupancy is not selected.

## 3. Tests
- [x] 3.1 Test the occupancy gate skips entries until the previous simulated exit index.
- [x] 3.2 Test default behavior remains unchanged when the gate is disabled.
- [x] 3.3 Test the three fixed profile names map to expected gate and exit settings.
- [x] 3.4 Test batch summary CSV/JSON records the occupancy settings and skip counter.

## 4. Real research run
- [x] 4.1 Run BTCUSDT `2024q1` early-falsification batches for all fixed profiles with unchanged thresholds; all failed the primary failing quarter, so remaining quarters are blocked/not run and not counted as passes.
- [x] 4.2 Produce/record the updated quarterly scorecard and artifact paths: `artifacts/occupancy-hold-exit-profile-comparison/early-falsified/summary.json` and `scorecard.csv`.
- [x] 4.3 State which quarters changed status versus the 5/8 reference: no quarter improved to pass; `2024q1` remains failed for all candidates on `max_drawdown_below_threshold`.
- [x] 4.4 If the result is below `8/8`, record the falsified verdict and remaining blockers.

## 5. Verification and archive
- [x] 5.1 Run strict OpenSpec validation for this change and all specs.
- [x] 5.2 Run relevant pytest/ruff/pyright/build checks or document exact blockers.
- [x] 5.3 Run self-review against the OpenSpec criteria and secret/live-safety constraints.
- [x] 5.4 Archive the checked research change as falsified negative evidence because all fixed candidates failed `2024q1` on `max_drawdown_below_threshold`.
- [x] 5.5 Create one scoped local commit if the working tree can be safely staged without unrelated changes.
