# Proposal

## Why
The current best BTCUSDT research profile, `conservative-v1-m15-slope-positive-max-trades-8`, improved the breakout hypothesis materially but still does not support it:

- passed windows: 5/8
- failed windows: 3/8
- hypothesis_supported: false

The latest bad-regime diagnostics identified recurring entry-time candidate buckets in failed windows:

- `atr_percentile -inf..0.25` is negative in all remaining failed windows.
- `2024q1` also loses heavily when `breakout_distance_atr > 1.0`.
- `2024q4` is profitable overall but drawdown-blocked, with losses concentrated in large candle-body buckets and one bad-day cluster.

This change tests a narrow next hypothesis: the strategy may pass more windows if it avoids selected low-volatility / bad continuation regimes while preserving the already-best lifecycle, feature, and risk controls.

## What Changes
- Add a small fixed set of research-only volatility/no-trade regime filter profiles.
- Apply candidate filters inside the backtest engine before trade creation, not as post-filtered CSVs, so lifecycle/risk state recalculates honestly.
- Keep the baseline comparison profile unchanged and reproducible.
- Export summary fields for the regime filter profile, settings, and skip counts.
- Run the quarterly 2023-2024 BTCUSDT comparison and report whether the hypothesis becomes supported.

## Non-Goals
- No arbitrary parameter/grid/Bayesian optimization.
- No ML, boosting, neural networks, or learned classifiers.
- No live trading, broker/exchange orders, balances, positions, private API, or production approval.
- No new market, symbol, timeframe, ETH, FX, or top-N expansion.
- No historical order book, стакан, L2 depth, DOM, spread, top-of-book, liquidity-wall, taker-flow, or trade-tape data. Microstructure data remains a separate future OpenSpec if OHLCV/context filters are insufficient.
- No default behavior change for `baseline`, `conservative-v1`, or existing profile names.
