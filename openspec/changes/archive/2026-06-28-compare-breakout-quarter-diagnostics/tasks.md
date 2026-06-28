## 1. Implementation
- [x] 1.1 Add quarter diagnostics artifact paths to portfolio summary output.
- [x] 1.2 Compute per-quarter candidate/accepted/skipped/blocker metrics.
- [x] 1.3 Add BTCUSDT/ETHUSDT context and fixed-universe breadth summaries from public historical data.
- [x] 1.4 Add optional relative-strength, cost-skip, confirmation/retest, and fast-failure ratios when upstream fields are available.
- [x] 1.5 Write comparison summary that separates passing, failed, blocked, and unknown windows.

## 2. Tests
- [x] 2.1 Test diagnostics serialize for mixed pass/fail/blocked windows.
- [x] 2.2 Test unavailable upstream fields are reported, not fabricated.
- [x] 2.3 Test diagnostics do not alter trade acceptance, PnL, or scorecard status.

## 3. Verification
- [x] 3.1 Run targeted portfolio diagnostics tests.
- [x] 3.2 Run strict OpenSpec validation.
- [x] 3.3 Run `git diff --check`.
