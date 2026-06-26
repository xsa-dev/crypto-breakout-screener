## MODIFIED Requirements
### Requirement: First crypto historical experiments use public unauthenticated data
The system SHALL support a first BTCUSDT crypto historical experiment scope using public unauthenticated market data only. The scope SHALL identify market `crypto`, instrument type `futures` or `perpetual`, execution timeframe `M15`, requested context timeframes `H1`, `H4`, and `D1`, and local report/export artifacts as the experiment output. The system SHALL support a public historical OHLCV downloader for the BTCUSDT M15/H1/H4/D1 first-slice experiment that writes deterministic CSV input for the existing canonical importer.

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

#### Scenario: Public BTCUSDT M15/H1/H4/D1 data is downloaded
- **WHEN** the user requests a public download for BTCUSDT M15/H1/H4/D1 with explicit UTC start and end timestamps
- **THEN** the downloader fetches public unauthenticated OHLCV/kline data for BTCUSDT linear/perpetual history for all four timeframes
- **AND** writes deterministic local CSV files compatible with the existing `Bar` importer
- **AND** records provider/source metadata including venue, endpoint family, category/instrument type, intervals, requested range, fetched ranges, page counts, and row counts without secrets

#### Scenario: Download range is invalid or open-ended
- **WHEN** the public downloader is called without explicit start/end timestamps or with an invalid range
- **THEN** it fails closed with an explicit validation error
- **AND** no completed dataset/report artifact is claimed

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

#### Scenario: Downloaded rows are deterministic before import
- **WHEN** public kline responses for any required timeframe contain reverse-ordered, duplicate, or overlapping paginated rows
- **THEN** the downloader writes CSV rows for each timeframe in deterministic ascending timestamp order with duplicate timestamps resolved by an explicit policy
- **AND** the existing importer can produce the same dataset hash for repeated equivalent downloads

### Requirement: Dataset manifests make crypto experiments reproducible
The system SHALL write a dataset manifest for each crypto historical experiment run. The manifest SHALL include source, market, instrument type, symbol, timeframe, requested and available context timeframes, start and end timestamps, bar count, dataset hash, feed gaps, normalization warnings, generated-at timestamp, and source metadata without secrets.

#### Scenario: Manifest is written with run artifacts
- **WHEN** a crypto historical experiment completes normalization and backtesting
- **THEN** a dataset manifest is written alongside the local report artifacts
- **AND** the manifest identifies the dataset hash used by the backtest report

#### Scenario: Manifest omits secrets
- **WHEN** a dataset manifest is generated
- **THEN** it contains no API keys, private endpoint URLs, authorization headers, private account identifiers, balances, positions, `.env` values, or credentials

#### Scenario: Downloader metadata is included
- **WHEN** a crypto experiment uses public downloaded CSV files
- **THEN** the manifest source metadata identifies the public provider, category/instrument type, intervals, requested range, fetched ranges, page counts, response row counts, accepted row counts, downloaded CSV paths, and warnings
- **AND** generated-at metadata may vary between runs while dataset hash and deterministic report identifiers remain stable for equivalent downloaded data
