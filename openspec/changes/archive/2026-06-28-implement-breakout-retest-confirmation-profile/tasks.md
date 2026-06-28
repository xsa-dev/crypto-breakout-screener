## 1. Implementation
- [x] 1.1 Add retest/confirmation profile settings.
- [x] 1.2 Implement confirmation blocker for missing/failed confirmation.
- [x] 1.3 Implement retest window, hold, and continuation decision.
- [x] 1.4 Preserve blocked/delayed candidates with reason codes.
- [x] 1.5 Export retest/confirmation counts and ratios.

## 2. Tests
- [x] 2.1 Test confirmation pass/fail behavior.
- [x] 2.2 Test missing retest blocks when required.
- [x] 2.3 Test failed retest blocks or exits with the required reason.
- [x] 2.4 Test no future bars beyond retest decision horizon are used.

## 3. Verification
- [x] 3.1 Run targeted retest/confirmation tests.
- [x] 3.2 Run strict OpenSpec validation.
- [x] 3.3 Run `git diff --check`.

## 4. Evidence
- [x] 4.1 Smoke-run `2024q1` with cached BTCUSDT public data, realistic-cost settings, and profile `conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-retest-3`.
- [x] 4.2 Record smoke artifact path `artifacts/retest-confirmation-profile-smoke/crypto/BTCUSDT/7e3501419068c37e/summary.json` and negative 2024q1 blockers (`net_profit_below_threshold`, `profit_factor_below_threshold`, `max_drawdown_below_threshold`).
