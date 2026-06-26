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

### Requirement: Crypto batch runner uses public unauthenticated BTCUSDT data only
The BTCUSDT batch experiment runner SHALL use only public unauthenticated market data and SHALL preserve the first crypto data boundaries for each window.

#### Scenario: Batch window data is loaded
- **WHEN** a batch window is evaluated
- **THEN** the runner uses BTCUSDT public unauthenticated OHLCV/kline input
- **AND** downloads or reuses M15, H1, H4, and D1 datasets for the window
- **AND** uses M15 as the execution/backtest input
- **AND** records H1/H4/D1 as context datasets in per-window manifests and batch summaries

#### Scenario: Unsupported batch scope is requested
- **WHEN** a user requests a non-BTCUSDT symbol, non-crypto market, FX instrument, private data source, or open-ended window
- **THEN** the runner fails closed with an explicit validation error
- **AND** no completed batch summary claims the unsupported request passed

### Requirement: Research gates use only simulated historical state
Backtest research gates SHALL use only deterministic simulated state available at or before the evaluated bar. They SHALL NOT read live broker state, private exchange/account data, environment credentials, or future bars.

#### Scenario: Gate state is updated during replay
- **WHEN** a backtest applies cooldown, daily trade count, daily PnL, or immediate re-entry gates
- **THEN** gate state is derived only from prior simulated trades and the current bar timestamp
- **AND** no future bar beyond the normal next-bar close used by the existing research model is inspected for entry gating

#### Scenario: Generated artifacts remain local
- **WHEN** lifecycle diagnostics and gated batch outputs are generated
- **THEN** generated data remains under ignored local artifact/report directories unless explicitly committed as small fixtures for tests

### Requirement: Crypto experiments expose context feature inputs without changing M15 execution
The BTCUSDT crypto historical experiment runner SHALL be able to pass downloaded H1/H4/D1 context CSVs into feature diagnostics while preserving M15 as the execution/backtest input for this research slice.

#### Scenario: Context datasets are supplied to diagnostics
- **WHEN** the crypto experiment runner has downloaded M15, H1, H4, and D1 public OHLCV CSVs for a window
- **THEN** it runs the backtest on the M15 execution CSV
- **AND** supplies H1/H4/D1 context CSV paths to feature diagnostics when supported
- **AND** the manifest and batch summary continue to record execution and context dataset paths separately

#### Scenario: Public-data boundary is preserved
- **WHEN** feature diagnostics are enabled for a crypto experiment or batch run
- **THEN** the runner remains public-data-only, read-only, and unauthenticated
- **AND** it does not read `.env`, private API keys, authorization headers, balances, positions, order history, or private endpoints

### Requirement: Batch summaries can audit feature-diagnostic artifacts
BTCUSDT batch summaries SHALL make feature-diagnostic availability auditable for every window without requiring manual inspection of the report directory.

#### Scenario: Feature diagnostics are present in a batch window
- **WHEN** a batch window completes with feature diagnostics exported
- **THEN** the summary row or referenced report artifact paths identify the entry feature snapshot, feature-bucket PnL, regime-bucket summary, and worst-day attribution artifacts
- **AND** the batch verdict remains research-only and separate from production approval

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

### Requirement: Breakout confirmation filters preserve no-lookahead semantics
Breakout confirmation filters SHALL use only information available at or before the delayed confirmation entry time.

#### Scenario: Confirmation needs future bars relative to original breakout
- **WHEN** a candidate breakout appears at bar `t`
- **AND** a profile requires confirmation from one or more later bar closes
- **THEN** the backtest MUST NOT enter at bar `t` using those later closes
- **AND** the earliest allowed entry is after the confirmation condition is observable.

#### Scenario: Confirmation fails before entry
- **WHEN** a pending breakout candidate fails the selected confirmation condition before entry
- **THEN** no trade is created for that candidate
- **AND** a deterministic machine-readable skip/cancel reason is counted.

### Requirement: Confirmation filters use OHLCV-only public research data
Breakout confirmation filters SHALL be computed from public OHLCV/context data already present in the research pipeline.

#### Scenario: Microstructure context is considered
- **WHEN** a confirmation idea requires order book, стакан, DOM, L2 depth, footprint, trade tape, taker-flow, private account state, or exchange credentials
- **THEN** that idea is out of scope for this change
- **AND** it must be proposed through a separate OpenSpec change before implementation.

### Requirement: Confirmation profiles preserve default behavior when disabled
Confirmation filter configuration SHALL be disabled by default.

#### Scenario: Reference profile runs
- **WHEN** the reference profile has no confirmation filter configured
- **THEN** existing signal evaluation, entry timing, risk gates, feature filters, and reporting behavior remain unchanged except for empty confirmation reporting fields where applicable.

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
