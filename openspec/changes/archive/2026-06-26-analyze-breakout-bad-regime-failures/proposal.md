# Proposal

## Why
The best current BTCUSDT breakout research profile is `conservative-v1-m15-slope-positive-max-trades-8`. It improved the comparison to 5/8 passed quarters and reduced worst drawdown to -1.1749, but the hypothesis remains unsupported because 2024q1, 2024q2, and 2024q4 still fail the research thresholds.

The previous slice showed that simple generic risk limits are not enough. The remaining failures need focused diagnostics to explain whether the strategy is breaking during specific bad regimes such as choppy reversals, volatility shocks, failed continuations, or trend exhaustion.

## What Changes
- Add local research diagnostics for failed-window attribution using the best current profile as the fixed baseline.
- Export per-window evidence for the remaining failed quarters:
  - 2024q1
  - 2024q2
  - 2024q4
- Aggregate failed trades and worst drawdown periods by existing entry/context features where available.
- Produce machine-readable diagnostics that can support or reject a later regime-filter hypothesis.

## Non-Goals
- Do not add a production trading approval.
- Do not add live trading, private exchange API usage, balances, orders, or positions.
- Do not train ML models, boosting, neural networks, or inference models.
- Do not run arbitrary parameter/grid/Bayesian optimization.
- Do not add ETH, FX, top-N symbols, or multi-market scope.
- Do not add historical order book, L2 depth, DOM, spread, or microstructure data sources in this diagnostic slice.
- Do not change default backtest behavior.
- Do not introduce a new trading filter in this change unless it is strictly diagnostic-only and disabled by default.

## Deferred Microstructure Research
Order book / стакан data may become useful for later breakout-failure research, especially for false breakouts, liquidity thinning, spread expansion, and weak follow-through. This change intentionally does not add that data dimension. If OHLCV/context diagnostics are insufficient, order book or taker-flow context should be proposed as a separate OpenSpec change with its own data availability, no-lookahead, storage, and artifact requirements.

## Expected Outcome
The result should be a diagnostic artifact set that explains the 2024q1/2024q2/2024q4 failures well enough to decide the next narrow hypothesis. The change may identify a promising no-trade regime, but it does not need to make the strategy pass all quarters.
