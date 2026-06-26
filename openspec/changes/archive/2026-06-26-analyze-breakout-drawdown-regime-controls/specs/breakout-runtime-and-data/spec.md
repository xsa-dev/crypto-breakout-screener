# breakout-runtime-and-data Specification Delta

## ADDED Requirements
### Requirement: Drawdown risk controls use realized state only
Research drawdown risk controls SHALL use only realized trade outcomes known at or before the next entry decision. They SHALL NOT use future bars, future PnL, future drawdown, future day totals, or future labels.

#### Scenario: Cross-midnight losing trade exits
- **WHEN** a losing trade enters before UTC midnight and exits after UTC midnight
- **THEN** realized loss counts toward the exit UTC day
- **AND** daily stop, loss streak, and post-loss cooldown logic for later entries uses the exit-day attribution

#### Scenario: Entry decision precedes future outcome
- **WHEN** a risk-control profile evaluates whether to allow an entry
- **THEN** it may use prior realized trades, current entry-time feature snapshot, and current configured state
- **AND** it SHALL NOT inspect the candidate trade outcome, next-bar exit, future worst-day contribution, or future window blockers

### Requirement: Drawdown risk-control research remains BTCUSDT public-data only
Drawdown risk-control comparison SHALL stay within the first crypto research boundary: BTCUSDT, public unauthenticated market data, M15 execution, H1/H4/D1 context datasets, and local artifacts.

#### Scenario: Credentials exist in the environment
- **WHEN** private exchange credentials or `.env` files exist locally
- **THEN** drawdown risk-control runs do not read or print private keys, authorization headers, balances, positions, orders, order history, or private endpoints
- **AND** only public CSV input or public unauthenticated market-data downloads are used
