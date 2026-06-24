## Why

The breakout strategy has approved domain specs but needs a concrete implementation foundation before later trading, persistence, and reporting slices can be built safely. This slice creates deterministic local primitives and tests without enabling live trading.

## What Changes

- Implement typed breakout configuration and baseline defaults for modes, symbols, timeframes, score weights, entry shares, and no-lookahead parameters.
- Implement canonical bar/tick/order-book DTOs, market data provider interfaces, and normalization utilities for UTC timestamps, deduplication, ordering, and gap marking.
- Implement level detection and validation for pivots, round numbers, daily high/low, cascade, and trendline candidates where source data supports them.
- Implement setup feature calculation and scoring for ATR/EMA/ADX, consolidation/protorgovka, slow approach, activity, density/proxy, scenario priority, and threshold classification.
- Add focused unit/replay tests proving closed-bar-only behavior and pivot right-window no-lookahead invariants.

## Non-Goals

- No live broker orders, real credentials, cloud delivery, or push/MR.
- No full state machine, risk manager, persistence schema, backtesting/reporting runtime, or operator UI in this slice.
- No concrete live exchange adapter beyond local interfaces and fakes needed by tests.
