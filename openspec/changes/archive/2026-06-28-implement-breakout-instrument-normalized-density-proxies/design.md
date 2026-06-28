# Design

## Parameter normalization

The breakout screener must avoid hardcoded per-symbol strategy thresholds. Symbol differences should be handled by normalized features:

- price distance as ATR multiple or basis points;
- breakout buffer as ATR/tick-size multiple;
- consolidation range as ATR multiple or rolling range percentile;
- volume as relative volume versus rolling median/percentile;
- volatility as rolling ATR percentile;
- wick/body quality as candle ratios;
- liquidity/cost pressure as relative friction and volume bucket.

Allowed per-symbol data:

- immutable metadata such as tick size, min notional, price precision, and provider symbol name;
- generated calibration artifacts computed only from the declared in-sample range;
- rolling statistics computed causally up to candidate time.

Forbidden:

- manual symbol lists such as “ETH gets threshold X, SOL gets threshold Y” unless they are immutable exchange metadata;
- calibration using out-of-sample or future bars;
- silent fallback to unreported defaults.

## Density/support proxy

When historical DOM/L2 is unavailable, density/support should be approximated from OHLCV and clearly labeled as `ohlcv_proxy`.

Required proxy components:

- `volume_near_level`: volume concentration while price trades within tolerance of the level;
- `relative_volume_expansion`: current volume versus rolling median/percentile;
- `body_dominance`: candle body size relative to full range, used to detect candles without excessive tails;
- `wick_rejection`: upper/lower wick ratio around the level, side-aware;
- `close_location_quality`: close near high for long breakout, close near low for short breakdown;
- `absorption_or_hold_proxy`: repeated tests of the level with shrinking adverse wick or improving closes.

The setup score may use these as density/support proxies but must expose that they are proxies, not real order book evidence.

## Reporting

Entry feature snapshots and score artifacts SHALL include:

- normalized threshold values used at candidate time;
- density source;
- density proxy component values;
- calibration artifact path when per-symbol calibration is used;
- missing-feature blockers when a proxy cannot be computed.

Quarter diagnostics SHOULD compare passing and failing windows by density proxy buckets and wick/body quality.
