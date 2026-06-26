# breakout-runtime-and-data Specification Delta

## ADDED Requirements
### Requirement: Feature-filter inputs preserve the no-lookahead boundary
Research feature filters SHALL evaluate only data known at or before the simulated entry timestamp. M15 feature inputs SHALL come from closed M15 bars at or before the entry bar. H1/H4/D1 context filters SHALL use context candles only after their close time is at or before the M15 entry timestamp, even when provider CSV timestamps represent candle open time.

#### Scenario: H1 open-time candle has not closed
- **WHEN** an M15 entry is evaluated at `10:15`
- **AND** an H1 candle has provider timestamp/open time `10:00` and close time `11:00`
- **THEN** that H1 candle is not available to feature filters for the `10:15` entry
- **AND** the filter uses the latest H1 candle whose close time is at or before `10:15`

#### Scenario: Missing context for required filter
- **WHEN** a profile requires H1 long trend alignment
- **AND** no H1 candle has closed at or before the entry timestamp
- **THEN** the entry is skipped with an explicit unavailable-context reason
- **AND** the M15-only baseline behavior remains unaffected when the H1 filter is disabled

### Requirement: Feature-filter research uses public BTCUSDT data only
Feature-filter comparison runs SHALL remain in the first crypto research boundary: public unauthenticated BTCUSDT data, M15 execution, and H1/H4/D1 context datasets.

#### Scenario: Feature-filter batch runs with credentials present
- **WHEN** private exchange credentials or `.env` files are present in the environment
- **THEN** feature-filter comparison runs do not read or print private keys, authorization headers, balances, positions, orders, order history, or private endpoints
- **AND** only public CSV input or public unauthenticated market-data downloads are used
