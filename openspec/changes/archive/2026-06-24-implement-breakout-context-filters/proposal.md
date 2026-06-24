## Why

The setup-scoring capability already requires context filters that can lower or block technically valid breakouts, but the current implementation only scores local bar/order-book features. A narrow implementation slice should add deterministic, local context-driver handling without introducing external market data integrations or live trading behavior.

## What Changes

- Add typed context-driver DTOs and configuration for deterministic setup-scoring context filters.
- Update setup scoring so opposing context drivers can either reduce score or block a setup with explicit rejection reasons.
- Add tests for no-context, score-penalty, hard-block, and side-symmetric behavior.

## Non-Goals

- No external DXY, US10Y, silver/gold, SP500/Nasdaq, exchange, broker, or live data integration.
- No changes to live execution, persistence, backtesting, or operator UI.
- No new permanent capability spec; this updates the existing `breakout-setup-scoring` capability.
