## 1. Data model and config

- [x] 1.1 Review current SQLite models/repositories and breakout DTOs.
- [x] 1.2 Implement config validation, version records, and stable config hashing.
- [x] 1.3 Implement or migrate persistence for bars, ticks, optional order book metadata, levels, features, signals, trade intents, orders, fills, positions, risk events, backtest runs, and decision traces as applicable to implemented slices.

## 2. Audit and replay

- [x] 2.1 Implement decision trace creation from level discovery through score, scenario, risk decision, execution/fake fill, position management, and exit.
- [x] 2.2 Implement dataset hashing and replay-required identifiers.
- [x] 2.3 Implement manual override and operator decision audit records.

## 3. Verification

- [x] 3.1 Add repository/migration tests for config versioning, trace links, risk rejection audit, fake fill chain, and replay hash determinism.
- [x] 3.2 Run `uv run ruff check .`.
- [x] 3.3 Run `uv run pyright` or document the local blocker if pyright is unavailable.
- [x] 3.4 Run `uv run pytest`.
- [x] 3.5 Run OpenSpec validation for this change and all specs.
