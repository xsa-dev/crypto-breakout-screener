# Proposal

## Why

The documented breakout screener should work across different crypto symbols without hardcoded per-coin thresholds. Coins differ by price scale, volatility, liquidity, wick behavior, and volume regime, so raw absolute thresholds can make one symbol look tradable and another impossible for the wrong reason.

The source documentation also highlights density/support around levels. Real order book/DOM density cannot be backtested when historical L2/order book data is unavailable. The system therefore needs explicit OHLCV-derived density proxies rather than pretending DOM was tested or dropping the density concept.

## What Changes

Add instrument-normalized parameters and density/support proxies for breakout setup scoring.

The change SHALL:

- prohibit symbol-specific hardcoded thresholds in strategy logic;
- express thresholds in normalized terms where possible: ATR, rolling percentiles, relative volume, tick/price scale, volatility regime, and liquidity buckets;
- allow data-driven per-symbol calibration from an in-sample window only when the calibration artifact is recorded and reused out-of-sample without future leakage;
- add OHLCV-derived density/support proxies for cases where order book data is unavailable;
- report whether density was measured from real DOM/L2 data or approximated from OHLCV.

## Success Criteria

- Strategy configuration has no hardcoded per-symbol magic values for entry thresholds, density, wick/body quality, volume, or ATR rules.
- Density proxy features are exported in entry feature snapshots and setup score artifacts.
- Reports label density source as `dom`, `ohlcv_proxy`, or `unavailable`.
- OHLCV density proxy includes at least volume near level, relative volume expansion, candle body dominance, wick rejection/absorption, and close-location quality.
- Backtests state whether per-symbol normalization used fixed defaults, rolling percentiles, or recorded calibration artifacts.

## Non-goals

- No claim that OHLCV proxies are equivalent to real order book density.
- No live/private exchange API, no historical L2 requirement, no symbol-by-symbol manual tuning, no future-data calibration, no threshold weakening.
