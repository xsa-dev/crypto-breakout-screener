## 1. Implementation
- [x] 1.1 Add lifecycle state fields to candidate/trade models or artifact rows.
- [x] 1.2 Populate lifecycle states from existing level/setup/breakout/feature data.
- [x] 1.3 Preserve skipped candidates with furthest lifecycle state and blocker.
- [x] 1.4 Add lifecycle state counts to portfolio summary and per-regime reports.

## 2. Tests
- [x] 2.1 Test lifecycle states are ordered and deterministic.
- [x] 2.2 Test skipped candidates keep furthest state and blocker.
- [x] 2.3 Test default profile behavior and PnL remain unchanged.

## 3. Verification
- [x] 3.1 Run targeted lifecycle/reporting tests.
- [x] 3.2 Run strict OpenSpec validation.
- [x] 3.3 Run `git diff --check`.
