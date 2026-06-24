## ADDED Requirements

### Requirement: Operation modes are explicit and staged
The system SHALL support `advisory-only`, `semi-auto`, and `full-auto` operation modes. The system SHALL allow historical backtest, paper trading, reduced-risk pilot, and production stages to be configured separately.

#### Scenario: Advisory-only mode
- **WHEN** a breakout setup is detected in `advisory-only` mode
- **THEN** the system records the signal and decision trace
- **AND** the system does not submit broker orders

#### Scenario: Semi-auto mode
- **WHEN** a risk-approved trade intent is produced in `semi-auto` mode
- **THEN** the system requires operator confirmation before execution

#### Scenario: Full-auto mode
- **WHEN** a risk-approved trade intent is produced in `full-auto` mode
- **THEN** the system may submit orders through the configured execution adapter
- **AND** the system records the automated execution decision

### Requirement: Market and timeframe scope is configurable
The system SHALL support configurable symbols and markets including forex, crypto, futures, CFD, stocks, and equivalent broker/API instruments when valid data and execution adapters exist. The baseline strategy SHALL support M15 execution context and H1/H4/D1 higher-timeframe context.

#### Scenario: Baseline timeframes configured
- **WHEN** the baseline configuration is loaded
- **THEN** the execution timeframe includes `M15`
- **AND** context timeframes include `H1`, `H4`, and `D1`

#### Scenario: Unsupported instrument
- **WHEN** a symbol has no compatible market-data provider or broker adapter
- **THEN** the system rejects that symbol with a configuration error before trading

### Requirement: Market data providers expose bars, ticks, and optional order book
The system SHALL use a `MarketDataProvider` abstraction for historical bars, streaming/recent ticks, and optional order book or density data. Missing optional order book data SHALL NOT break core breakout detection but SHALL be reflected in density scoring.

#### Scenario: Bars are fetched
- **WHEN** historical analysis or backtest requests bars
- **THEN** the provider returns canonical OHLCV bars with timestamp, open, high, low, close, volume, spread/source metadata when available

#### Scenario: Ticks are fetched
- **WHEN** realtime breakout confirmation requires tick data
- **THEN** the provider returns canonical ticks with timestamp, bid, ask, last, volume/flags when available

#### Scenario: Order book is unavailable
- **WHEN** density scoring is requested and no order book source is configured
- **THEN** the system records density as unavailable or uses an approved configured proxy

### Requirement: Data normalization prevents inconsistent inputs
The normalizer SHALL convert timestamps to UTC, deduplicate repeated bars/ticks, validate ordering, resample only through configured rules, and mark data gaps.

#### Scenario: Duplicate event received
- **WHEN** a duplicate bar or tick arrives from a provider
- **THEN** the normalizer emits one canonical event or updates it idempotently according to configured source precedence

#### Scenario: Feed gap detected
- **WHEN** expected bars or ticks are missing beyond the configured tolerance
- **THEN** the system records a feed-gap event
- **AND** live execution is blocked or degraded according to operations policy

### Requirement: No-lookahead invariant is enforced
The system MUST NOT use future bars, future ticks, or unconfirmed right-window pivots when producing online signals, risk decisions, or live orders.

#### Scenario: Pivot requires right-window bars
- **WHEN** a pivot candidate depends on `pivot_right_bars=3`
- **THEN** the pivot becomes valid only after three later bars have closed

#### Scenario: Backtest uses same online information boundary
- **WHEN** a backtest evaluates a bar
- **THEN** the strategy only sees data that would have been available at that historical time
