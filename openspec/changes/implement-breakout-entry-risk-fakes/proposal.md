## Why

After the foundation slice exists, the project needs a deterministic lifecycle engine that turns validated setups into entry intents, applies blocking risk controls, and proves execution behavior with fakes before any live adapter is considered.

## What Changes

- Implement the required finite state machine and transition logging.
- Implement pre-entry, at-level, and post-breakout entry intents with default 30/30/40 shares.
- Implement breakout confirmation, retest validation, false-breakout handling, add-ons, stop movement, and 30/50/20 partial exits.
- Implement a blocking Risk Manager for position sizing, add-on budget, daily loss, max-open-position limits, and feed/broker degraded-state rejections.
- Implement fake execution adapters and reconciliation tests only; keep live broker adapters out of scope.

## Non-Goals

- No live Bybit, MT5, broker, exchange, or terminal adapter.
- No production `full_auto` enablement.
- No persistence migration except minimal in-memory records or DTOs needed for tests.
