# breakout-runtime-and-data Specification Delta

## ADDED Requirements
### Requirement: Forward-path labels preserve entry-time no-lookahead
Forward-path, MAE, MFE, and synthetic holding-horizon values SHALL be treated as offline diagnostic labels. They SHALL NOT be used by entry filters, risk controls, confirmation filters, sizing, or live/research signal generation in this change.

#### Scenario: Forward bars are inspected for diagnostics
- **WHEN** the diagnostic exporter computes values for bars after a simulated entry
- **THEN** those future bars are used only after the trade has already been produced by the backtest engine
- **AND** the values are written only to diagnostic artifacts
- **AND** no entry decision, skip reason, quantity, or realized exit is changed by those labels

### Requirement: Forward-path diagnostics remain in public BTCUSDT scope
Forward-path diagnostics SHALL remain in the first crypto research boundary: BTCUSDT, public unauthenticated OHLCV data, M15 execution, H1/H4/D1 context metadata when already available, and local artifacts.

#### Scenario: Credentials or private data are present locally
- **WHEN** private exchange credentials, `.env` files, or account data exist on the machine
- **THEN** forward-path diagnostics do not read, require, print, or persist private keys, authorization headers, balances, positions, orders, order history, or private endpoints
- **AND** only public OHLCV CSV input or public unauthenticated market-data downloads are used

### Requirement: Forward-path scope excludes microstructure dimensions
Forward-path diagnostics SHALL not introduce new historical microstructure data dimensions.

#### Scenario: User later asks for order-flow context
- **WHEN** a later research question requires order book, стакан, DOM, L2 depth, footprint, taker-flow, trade tape, spread, or liquidity-wall context
- **THEN** that data dimension is out of scope for this change
- **AND** it requires a separate OpenSpec change with explicit data availability, no-lookahead, storage, and artifact requirements
