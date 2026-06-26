# breakout-runtime-and-data Specification Delta

## ADDED Requirements
### Requirement: Volatility-regime filters use entry-time information only
Volatility/no-trade regime filters SHALL evaluate only feature values available at the candidate entry timestamp.

#### Scenario: ATR-percentile filter is evaluated
- **WHEN** a candidate entry is evaluated by an ATR-percentile regime filter
- **THEN** the decision uses only the precomputed entry-time `feature_atr_percentile` snapshot
- **AND** it does not inspect future PnL, future drawdown, future labels, or the candidate trade outcome

#### Scenario: Breakout-distance or candle-body filters are evaluated
- **WHEN** a candidate entry is evaluated by breakout-distance or candle-body regime filters
- **THEN** the decision uses only current/closed-bar entry-time feature snapshot values
- **AND** higher-timeframe context remains aligned by context candle close time, not provider open timestamp

### Requirement: Volatility-regime filters remain public OHLCV/context only
This change SHALL NOT introduce historical order book, стакан, L2 depth, DOM, spread, top-of-book, liquidity-wall, taker-flow, trade-tape, private API, account, order, balance, or position data.

#### Scenario: Microstructure context is requested
- **WHEN** a later hypothesis requires order book, стакан, L2, DOM, taker-flow, or trade-tape context
- **THEN** that data dimension is out of scope for this change
- **AND** it requires a separate OpenSpec change with explicit data availability, storage, no-lookahead, and artifact requirements
