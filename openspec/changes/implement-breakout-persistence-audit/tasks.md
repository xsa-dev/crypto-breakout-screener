## 1. Data model and config

- [ ] 1.1 Review current SQLite models/repositories and breakout DTOs.
- [ ] 1.2 Implement config validation, version records, and stable config hashing.
- [ ] 1.3 Implement or migrate persistence for bars, ticks, optional order book metadata, levels, features, signals, trade intents, orders, fills, positions, risk events, backtest runs, and decision traces as applicable to implemented slices.

## 2. Audit and replay

- [ ] 2.1 Implement decision trace creation from level discovery through score, scenario, risk decision, execution/fake fill, position management, and exit.
- [ ] 2.2 Implement dataset hashing and replay-required identifiers.
- [ ] 2.3 Implement manual override and operator decision audit records.

## 3. Verification

- [ ] 3.1 Add repository/migration tests for config versioning, trace links, risk rejection audit, fake fill chain, and replay hash determinism.
- [ ] 3.2 Run `uv run ruff check .`.
- [ ] 3.3 Run `uv run pyright` or document the local blocker if pyright is unavailable.
- [ ] 3.4 Run `uv run pytest`.
- [ ] 3.5 Run OpenSpec validation for this change and all specs.
