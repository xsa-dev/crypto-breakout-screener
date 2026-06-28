# Design

## Heikin-Ashi transform

For each symbol/timeframe, compute a deterministic transformed series:

- `ha_close = (open + high + low + close) / 4`;
- `ha_open = (previous_ha_open + previous_ha_close) / 2`, seeded deterministically from the first raw bar;
- `ha_high = max(high, ha_open, ha_close)`;
- `ha_low = min(low, ha_open, ha_close)`.

The transform must be causal: bar `t` uses only raw bars up to `t` and previous Heikin-Ashi values.

## Allowed use

Allowed Heikin-Ashi-derived features:

- `ha_body_ratio`;
- `ha_upper_wick_ratio`;
- `ha_lower_wick_ratio`;
- `ha_close_location`;
- `ha_color`;
- `ha_color_streak`;
- `ha_trend_persistence`;
- `ha_compression`;
- `ha_reversal_hint`;
- `ha_failed_continuation_hint`.

These features can contribute to setup score, quarter diagnostics, density proxy analysis, and fast-failure heuristics when an opt-in profile enables them.

## Named profiles

Implement named profiles rather than ad hoc flags:

- `heikin-ashi-trend-filter-v1`
  - Purpose: entry-time trend/noise filter.
  - Uses: `ha_color`, `ha_color_streak`, `ha_body_ratio`, `ha_trend_persistence`, and side-aware wick ratios.
  - Must block weak/noisy candidates with machine-readable feature blockers.

- `heikin-ashi-confirmation-v1`
  - Purpose: breakout confirmation support.
  - Uses: Heikin-Ashi continuation, body dominance, close-location quality, and absence of strong opposite wick after raw breakout.
  - Must integrate with existing confirmation reporting and keep raw OHLCV confirmation fields available.

- `heikin-ashi-exit-v1`
  - Purpose: exit/hold decision support.
  - Uses: Heikin-Ashi reversal hint, failed-continuation hint, color flip, and weakening body quality.
  - Must alter exit/hold decisions only when enabled and must price exits using raw OHLCV.

Combined `gate_profile` names may wrap these profiles, but reports must expose the active Heikin-Ashi component profile names separately from raw feature, confirmation, and exit profile names.

## Forbidden use

Heikin-Ashi values must not be used for:

- entry fill price;
- exit fill price;
- stop price accounting;
- target fill accounting;
- spread/slippage/funding calculations;
- portfolio equity curve;
- max drawdown or profit factor accounting.

All economic accounting remains raw OHLCV-based.

## Reporting

Artifacts SHALL include:

- whether Heikin-Ashi features were enabled;
- active Heikin-Ashi profile names;
- transform settings/seed rule;
- raw versus Heikin-Ashi feature columns where relevant;
- score contribution or diagnostic bucket using Heikin-Ashi features;
- a warning if a report uses Heikin-Ashi features but no raw-price accounting artifact is present.

## Relationship to density proxies

Heikin-Ashi can help classify candle quality and continuation/noise, but it does not replace DOM/L2 density. If density is approximated without order book data, the density source remains `ohlcv_proxy`.
