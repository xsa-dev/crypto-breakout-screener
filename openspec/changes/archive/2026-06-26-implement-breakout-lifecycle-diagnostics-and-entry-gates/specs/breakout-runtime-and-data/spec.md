## ADDED Requirements
### Requirement: Research gates use only simulated historical state
Backtest research gates SHALL use only deterministic simulated state available at or before the evaluated bar. They SHALL NOT read live broker state, private exchange/account data, environment credentials, or future bars.

#### Scenario: Gate state is updated during replay
- **WHEN** a backtest applies cooldown, daily trade count, daily PnL, or immediate re-entry gates
- **THEN** gate state is derived only from prior simulated trades and the current bar timestamp
- **AND** no future bar beyond the normal next-bar close used by the existing research model is inspected for entry gating

#### Scenario: Generated artifacts remain local
- **WHEN** lifecycle diagnostics and gated batch outputs are generated
- **THEN** generated data remains under ignored local artifact/report directories unless explicitly committed as small fixtures for tests
