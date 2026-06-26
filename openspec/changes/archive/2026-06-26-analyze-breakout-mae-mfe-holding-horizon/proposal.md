# Proposal

## Why
The current BTCUSDT breakout research line has tested multiple entry-filter ideas, but the hypothesis is still not supported:

- current best: `conservative-v1-m15-slope-positive-max-trades-8`
- passed windows: 5/8
- failed windows: 3/8
- hypothesis_supported: false

Subsequent fixed volatility/no-trade filters and false-breakout confirmation filters did not improve the passed-window count. This suggests that adding another entry filter may be the wrong next step.

The existing backtest lifecycle still realizes trades with a very short holding model. A breakout hypothesis is fundamentally a continuation hypothesis, so the next research step should diagnose what happens after entries before adding more filters: whether favorable excursion appears after 1/2/4/8/16 bars, whether adverse excursion dominates, whether failed windows differ from passed windows, and whether current next-bar exits are mismatched with the signal.

## What changes
Add deterministic, diagnostic-only forward-path artifacts for the current best BTCUSDT profile:

- per-trade forward returns over fixed M15 horizons;
- MAE/MFE over fixed M15 horizons;
- time-to-MFE/time-to-MAE diagnostics;
- return-to-breakout-level diagnostics;
- holding-horizon synthetic PnL summaries for fixed horizons;
- passed-vs-failed window comparison summaries.

The diagnostics must not change trade selection, sizing, exits, risk controls, or the research verdict logic.

## Non-goals
- No new entry filters or no-trade filters.
- No changes to production/live trading behavior.
- No private exchange API, balances, orders, positions, `.env`, or authorization headers.
- No order book, стакан, DOM, L2 depth, footprint, taker-flow, or trade tape data.
- No ML, boosting, neural networks, LLM trading decisions, or automatic threshold optimization.
- No new market, symbol, or timeframe scope.
- No implementation of new exit rules in this change; exit/holding changes may be proposed later only if diagnostics support them.

## Success criteria
- The diagnostics are deterministic and no-lookahead-safe.
- The existing best profile can be re-run across quarterly 2023-2024 windows with the new artifacts enabled.
- The output answers whether the breakout signal has forward continuation after entry and whether a holding-horizon follow-up is justified.
- OpenSpec validation, tests, lint, type checks, and git diff hygiene pass.
