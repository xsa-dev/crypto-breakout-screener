# Proposal

## Why

The documented breakout screener needs a way to reduce candle noise and compare trend/continuation quality across symbols without hardcoded per-coin parameters. Heikin-Ashi candles can be useful as a derived feature view for trend persistence, body/wick quality, compression, and failed-continuation detection.

Heikin-Ashi must not replace real OHLCV for execution, PnL, costs, stops, or historical fills. It is a feature layer only.

## What Changes

Add an opt-in Heikin-Ashi feature view for breakout research.

The feature view SHALL:

- compute deterministic Heikin-Ashi OHLC from raw OHLCV bars;
- preserve raw OHLCV as the source of truth for execution, stops, fills, costs, PnL, and drawdown;
- expose Heikin-Ashi body/wick ratios, color/side continuity, trend persistence, compression, and reversal/failure hints;
- allow setup scoring and diagnostics to compare raw-candle features versus Heikin-Ashi-derived features;
- report when Heikin-Ashi features were active.

The implementation SHALL expose these named profiles:

- `heikin-ashi-trend-filter-v1`: uses Heikin-Ashi trend persistence/body quality as an entry-time feature filter;
- `heikin-ashi-confirmation-v1`: uses Heikin-Ashi continuation and close/body quality as breakout confirmation support;
- `heikin-ashi-exit-v1`: uses Heikin-Ashi reversal or failed-continuation hints as exit/hold decision support while pricing exits on raw OHLCV.

## Success Criteria

- Historical runs can enable or disable Heikin-Ashi features without changing raw price accounting.
- The CLI/programmatic runner can select `heikin-ashi-trend-filter-v1`, `heikin-ashi-confirmation-v1`, and `heikin-ashi-exit-v1` as named profiles or as documented components of a combined `gate_profile`.
- Entry feature snapshots include Heikin-Ashi fields when enabled.
- Setup score/reporting can include Heikin-Ashi body dominance, wick rejection, color streak, and continuation/failure fields.
- Reports explicitly state that Heikin-Ashi was used as a derived feature view, not as executable market prices.

## Non-goals

- No Heikin-Ashi execution prices, no PnL from transformed candles, no replacement of raw OHLCV, no threshold weakening, no private/live API, no claim that Heikin-Ashi alone proves robustness.
