## 1. Implementation
- [x] 1.1 Audit breakout configuration and remove/forbid symbol-specific hardcoded strategy thresholds.
- [x] 1.2 Add normalized feature helpers for ATR distance, rolling percentiles, relative volume, body/wick ratios, and close location.
- [x] 1.3 Add OHLCV density proxy components: volume near level, relative volume expansion, body dominance, wick rejection, close-location quality, and absorption/hold proxy.
- [x] 1.4 Export density source and proxy components in entry feature snapshots and setup score artifacts.
- [x] 1.5 Record calibration artifact paths when data-driven per-symbol calibration is used.
- [x] 1.6 Add missing-feature blockers instead of silently accepting candidates when required proxy inputs are unavailable.

## 2. Tests
- [x] 2.1 Test normalized features are scale-invariant across synthetic low-price and high-price symbols.
- [x] 2.2 Test no manual per-symbol strategy thresholds are required for the proxy score.
- [x] 2.3 Test candle body dominance and wick rejection behave side-aware for long and short candidates.
- [x] 2.4 Test density source is reported as `ohlcv_proxy` when DOM/L2 data is absent.
- [x] 2.5 Test calibration cannot use future/out-of-sample bars.

## 3. Verification
- [x] 3.1 Run targeted setup scoring and feature snapshot tests.
- [x] 3.2 Run strict OpenSpec validation.
- [x] 3.3 Run `git diff --check`.
