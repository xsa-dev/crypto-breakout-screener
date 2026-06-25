# breakout-runtime-and-data Specification

## Purpose
Define the safe runtime modes, canonical market-data contracts, provider boundaries, normalization rules, and no-lookahead invariants used by the breakout strategy.
## Requirements
### Requirement: Operation modes are explicit and staged
The system SHALL implement typed local configuration for `advisory_only`, `semi_auto`, and `full_auto` operation modes while keeping live `full_auto` execution blocked by deferred-scope gates until a later approved execution change. The system SHALL allow historical backtest, paper trading, reduced-risk pilot, and production stages to be configured separately.

#### Scenario: Baseline mode is safe
- **WHEN** the baseline breakout configuration is loaded during this foundation slice
- **THEN** the operation mode defaults to `semi_auto`
- **AND** no broker order can be submitted by foundation components

#### Scenario: Advisory-only mode
- **WHEN** a breakout setup is detected in `advisory_only` mode
- **THEN** the system records the signal and decision trace
- **AND** the system does not submit broker orders

#### Scenario: Semi-auto mode
- **WHEN** a risk-approved trade intent is produced in `semi_auto` mode
- **THEN** the system requires operator confirmation before execution

#### Scenario: Full-auto mode remains gated
- **WHEN** a risk-approved trade intent is produced in `full_auto` mode before the deferred execution change is approved
- **THEN** the system rejects live broker execution through the deferred-scope gate
- **AND** the system records the blocked automated execution decision

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
The system SHALL expose local provider protocols/interfaces for historical bars, recent or streaming ticks, and optional order-book/density data using canonical DTOs that can be implemented by fakes in tests before any live adapter is approved. Missing optional order book data SHALL NOT break core breakout detection but SHALL be reflected in density scoring.

#### Scenario: Fake provider is sufficient for tests
- **WHEN** foundation tests evaluate breakout levels or setup scores
- **THEN** they can use an in-memory provider without network credentials
- **AND** the provider returns canonical bars/ticks accepted by the normalizer

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
The normalizer SHALL implement UTC conversion, deterministic deduplication, ordering validation, configured resampling/gap marking, and metadata propagation for canonical bars and ticks.

#### Scenario: Out-of-order input is normalized or rejected
- **WHEN** provider data arrives out of timestamp order
- **THEN** the normalizer emits deterministic ordered events or raises an explicit validation error according to configuration

#### Scenario: Duplicate event received
- **WHEN** a duplicate bar or tick arrives from a provider
- **THEN** the normalizer emits one canonical event or updates it idempotently according to configured source precedence

#### Scenario: Feed gap detected
- **WHEN** expected bars or ticks are missing beyond the configured tolerance
- **THEN** the system records a feed-gap event
- **AND** live execution is blocked or degraded according to operations policy

### Requirement: No-lookahead invariant is enforced
The foundation implementation SHALL include tests proving online calculations do not use future bars, future ticks, or unconfirmed pivot right-window bars. The system MUST NOT use future bars, future ticks, or unconfirmed right-window pivots when producing online signals, risk decisions, or live orders.

#### Scenario: Closed-bar-only signal calculation is tested
- **WHEN** an online setup is evaluated at a historical bar
- **THEN** tests verify only closed bars available at that timestamp are passed to level and setup calculations

#### Scenario: Pivot requires right-window bars
- **WHEN** a pivot candidate depends on `pivot_right_bars=3`
- **THEN** the pivot becomes valid only after three later bars have closed

#### Scenario: Backtest uses same online information boundary
- **WHEN** a backtest evaluates a bar
- **THEN** the strategy only sees data that would have been available at that historical time

### Requirement: First crypto historical experiments use public unauthenticated data
The system SHALL support a first BTCUSDT crypto historical experiment scope using public unauthenticated market data only. The scope SHALL identify market `crypto`, instrument type `futures` or `perpetual`, execution timeframe `M15`, requested context timeframes `H1`, `H4`, and `D1`, and local report/export artifacts as the experiment output.

#### Scenario: BTCUSDT first experiment scope is loaded
- **WHEN** the first crypto historical experiment runner is configured with defaults
- **THEN** the market is `crypto`
- **AND** the first symbol is `BTCUSDT`
- **AND** the instrument type is `perpetual` or `futures`
- **AND** the execution timeframe is `M15`
- **AND** context timeframe metadata includes `H1`, `H4`, and `D1`
- **AND** the output target is a local backtest report/export artifact set

#### Scenario: Public data source is required
- **WHEN** the first crypto experiment loads market data
- **THEN** it uses public unauthenticated market-data input such as a CSV importer or public OHLCV endpoint
- **AND** it does not require API keys, private account state, authorization headers, balances, positions, private order history, or `.env` credentials

### Requirement: Historical crypto bars are normalized into canonical Bar records
The system SHALL normalize historical crypto OHLCV rows into the existing canonical `Bar` schema with UTC timestamps, deterministic ordering/deduplication, OHLC validation, gap diagnostics, and source metadata.

#### Scenario: CSV rows are normalized
- **WHEN** BTCUSDT historical OHLCV rows are imported from CSV
- **THEN** each accepted row is converted to a canonical `Bar` with symbol, timeframe, UTC timestamp, open, high, low, close, volume, and source metadata when available

#### Scenario: Duplicate or out-of-order bars are handled deterministically
- **WHEN** imported bars contain duplicate symbol/timeframe/timestamp keys or arrive out of timestamp order
- **THEN** the loader deduplicates and orders them deterministically or rejects them according to an explicit policy
- **AND** repeated imports of the same source data produce the same normalized sequence and dataset hash

#### Scenario: Invalid OHLC row is detected
- **WHEN** a row has inconsistent OHLC values such as high below open/close/low or low above open/close/high
- **THEN** the loader rejects the row or records a normalization error according to the configured policy
- **AND** invalid data is not silently passed to the backtest engine

#### Scenario: Gaps are recorded
- **WHEN** normalized bars have timestamp gaps larger than the expected timeframe interval
- **THEN** the system records feed-gap diagnostics for the dataset manifest

### Requirement: Dataset manifests make crypto experiments reproducible
The system SHALL write a dataset manifest for each crypto historical experiment run. The manifest SHALL include source, market, instrument type, symbol, timeframe, requested and available context timeframes, start and end timestamps, bar count, dataset hash, feed gaps, normalization warnings, generated-at timestamp, and source metadata without secrets.

#### Scenario: Manifest is written with run artifacts
- **WHEN** a crypto historical experiment completes normalization and backtesting
- **THEN** a dataset manifest is written alongside the local report artifacts
- **AND** the manifest identifies the dataset hash used by the backtest report

#### Scenario: Manifest omits secrets
- **WHEN** a dataset manifest is generated
- **THEN** it contains no API keys, private endpoint URLs, authorization headers, private account identifiers, balances, positions, `.env` values, or credentials
