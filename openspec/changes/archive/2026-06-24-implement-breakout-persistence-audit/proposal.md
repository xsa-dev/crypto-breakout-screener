## Why

Breakout decisions need to be explainable and reproducible. The current strategy components need persistent configuration versions, decision traces, and audit records before backtesting, operator review, or semi-auto confirmation can be reliable.

## What Changes

- Implement config validation, version hashes, and baseline parameter serialization.
- Implement persistence entities/repositories or migrations for canonical market data, levels, features, signals, trade intents, risk events, orders/fills/positions when fake execution exists, backtest metadata, and decision traces.
- Implement deterministic dataset/config hashing for replay.
- Implement audit records for operator confirmations, rejections, manual overrides, and parameter changes.

## Non-Goals

- No live broker credentials or production database deployment.
- No full reporting UI; persistence APIs or repository methods are enough for this slice.
