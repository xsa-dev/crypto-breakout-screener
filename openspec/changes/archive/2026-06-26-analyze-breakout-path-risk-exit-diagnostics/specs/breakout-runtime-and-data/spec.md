# breakout-runtime-and-data Specification Delta

## ADDED Requirements
### Requirement: Path-risk labels preserve no-lookahead runtime semantics
Path-risk, threshold-ordering, break-even, and trailing-touch labels SHALL be offline diagnostic labels only and SHALL NOT influence runtime entry, risk, sizing, exit, actual PnL, or verdict decisions.

#### Scenario: Path-risk labels are unavailable to decision logic
- **GIVEN** a trade candidate being evaluated by entry, confirmation, feature, risk, sizing, or exit logic
- **WHEN** path-risk diagnostics are enabled
- **THEN** future-bar path-risk labels are not accessible to that decision logic
- **AND** the labels are computed only after the trade list already exists.

#### Scenario: Missing entry-time ATR is explicit
- **GIVEN** a trade lacks an entry-time ATR value required for ATR-threshold labels
- **WHEN** path-risk diagnostics are generated
- **THEN** threshold labels for that trade/horizon are marked unavailable
- **AND** the unavailable reason is machine-readable
- **AND** the implementation does not infer ATR from future bars.

#### Scenario: Insufficient future bars are explicit
- **GIVEN** a trade does not have enough future closed bars for a configured horizon
- **WHEN** path-risk diagnostics are generated
- **THEN** the diagnostic row is marked unavailable for that horizon
- **AND** the unavailable reason is machine-readable
- **AND** aggregate summaries include unavailable counts.

### Requirement: Path-risk diagnostics remain public-data scoped
Path-risk diagnostics SHALL use only already-loaded public OHLCV data and already-produced trade metadata.

#### Scenario: Private data is not required
- **GIVEN** private exchange credentials, `.env` files, or account data exist on the machine
- **WHEN** path-risk diagnostics are generated
- **THEN** diagnostics do not read, require, print, or persist private keys, authorization headers, balances, positions, orders, order history, or private endpoints.
