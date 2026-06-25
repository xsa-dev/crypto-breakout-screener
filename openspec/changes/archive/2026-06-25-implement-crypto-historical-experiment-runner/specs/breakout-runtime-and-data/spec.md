## ADDED Requirements
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
