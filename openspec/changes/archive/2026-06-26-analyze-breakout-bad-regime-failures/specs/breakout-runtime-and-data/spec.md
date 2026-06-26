# breakout-runtime-and-data Specification Delta

## ADDED Requirements
### Requirement: Bad-regime candidate features preserve no-lookahead semantics
Any diagnostic bucket described as a candidate entry-time regime feature SHALL be computable from data known at or before the entry decision.

#### Scenario: Candidate no-trade regime is identified
- **WHEN** diagnostics identify a candidate bad-regime bucket for later testing
- **THEN** the bucket definition is based on entry-time market/context fields or prior realized state only
- **AND** future trade PnL, future drawdown, future day totals, and future labels are not part of the candidate feature definition
- **AND** post-run outcome metrics are clearly labeled as attribution evidence, not entry-time inputs

### Requirement: Bad-regime diagnostics remain public-data local research
Bad-regime diagnostics SHALL stay within BTCUSDT public market data and local artifact processing.

#### Scenario: Private credentials exist locally
- **WHEN** `.env` files, private keys, or exchange credentials exist in the repository or shell environment
- **THEN** bad-regime diagnostics do not read, print, serialize, or depend on private keys, authorization headers, balances, positions, orders, order history, or private endpoints

#### Scenario: Order book context is considered
- **WHEN** a later research question requires historical order book, стакан, L2 depth, DOM, spread, top-of-book, liquidity-wall, taker-flow, or trade-tape context
- **THEN** that data dimension is out of scope for this change
- **AND** it must be proposed through a separate OpenSpec change with explicit data availability, no-lookahead, storage, and artifact requirements
