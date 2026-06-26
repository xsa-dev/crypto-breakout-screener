# implement-breakout-context-feature-diagnostics

## Why
The lifecycle-gated BTCUSDT quarterly research rerun substantially reduced overtrading, but did not validate the trading hypothesis:

- baseline: 69,866 trades, worst drawdown about -3.63, 8/8 windows blocked
- conservative-v1: 7,193 trades, worst drawdown about -1.68, 6/8 windows still blocked
- all conservative-v1 windows became net-profitable, but most still failed max-drawdown thresholds

This means lifecycle gates address churn, but the strategy still lacks enough context discrimination. Before adding boosting/neural models or changing the live strategy, the local research pipeline needs deterministic entry-time feature diagnostics to identify which market regimes and technical conditions produce the remaining drawdown.

## What Changes
This change adds a research-only feature diagnostics layer for BTCUSDT breakout backtests and batch experiments.

It will:

- compute deterministic entry-time feature snapshots for every simulated trade using only data available at or before the entry bar;
- include existing setup features and additional technical/context features such as ATR regime, EMA distance/slope, breakout distance, candle body/range quality, volume/activity proxies, recent realized lifecycle state, and optional H1/H4/D1 context features when context CSVs are supplied;
- export machine-readable feature snapshot and feature-bucket diagnostic artifacts;
- run a new BTCUSDT quarterly comparison that reports baseline, conservative-v1 gates, and conservative-v1 plus feature-diagnostic summaries;
- keep all outputs local, public-data-only, unauthenticated, and research-only.

This change will not:

- add ML model training, LightGBM/XGBoost/CatBoost, neural networks, or model dependencies;
- add optimization search or automatically selected thresholds;
- change default trade selection or production strategy behavior;
- enable private exchange APIs, live trading, broker adapters, positions, balances, orders, or full-auto execution;
- broaden the market scope beyond BTCUSDT quarterly public-data experiments;
- claim production OOS approval even if diagnostics identify promising filters.

The follow-up after this change should decide whether to implement simple rule filters or a separate ML research-filter OpenSpec change based on the diagnostic evidence.
