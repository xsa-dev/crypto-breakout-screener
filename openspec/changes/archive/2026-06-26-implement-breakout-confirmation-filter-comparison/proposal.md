# Proposal

## Why
The current best BTCUSDT breakout research profile remains `conservative-v1-m15-slope-positive-max-trades-8`:

- passed windows: 5/8
- failed windows: 3/8
- hypothesis_supported: false

The previous volatility/no-trade regime comparison did not improve the reference profile. Fixed ATR/body/breakout-distance threshold blocks produced at most 3/8 passed windows and sometimes damaged otherwise profitable quarters.

The next evidence-based hypothesis is that the strategy enters too early on first-touch breakouts. Instead of blocking broad volatility buckets, this change tests whether requiring deterministic OHLCV confirmation of the breakout reduces false breakouts and improves quarterly robustness.

## What Changes
Implement a fixed comparison of confirmation profiles on top of the current best profile:

- reference: `conservative-v1-m15-slope-positive-max-trades-8`
- `conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1`
- `conservative-v1-m15-slope-positive-max-trades-8-confirm-close-2`
- `conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-closepos70`
- `conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-no-return-inside-range`

The confirmation filters SHALL use only public OHLCV and already available feature/context data. They SHALL be evaluated causally by delaying entry until confirmation is known; they SHALL NOT inspect future bars while entering at the original breakout bar.

## Out of Scope
- No live trading or production approval.
- No private exchange API, balances, orders, positions, account state, or `.env` reads.
- No order book, стакан, DOM, L2 depth, footprint, taker-flow, or trade-tape data.
- No ML, boosting, neural nets, LLM trading decisions, or automatic optimization.
- No arbitrary threshold/grid/Bayesian search.
- No new market, symbol, or timeframe family; BTCUSDT public crypto research remains the scope.
- No short-side strategy or portfolio construction.

## Expected Evidence
The change is successful only if the quarterly batch artifacts show an improved or supported hypothesis relative to the reference. If the profiles do not improve the reference, the implementation still completes as a falsified research slice with archived evidence.
