## MODIFIED Requirements

### Requirement: First crypto historical experiments use public unauthenticated data
The system SHALL support a first BTCUSDT crypto historical experiment scope using public unauthenticated market data only. The scope SHALL identify market `crypto`, instrument type `futures` or `perpetual`, execution timeframe `M15`, requested context timeframes `H1`, `H4`, and `D1`, and local report/export artifacts as the experiment output. The system SHALL support a public historical OHLCV downloader for the BTCUSDT M15/H1/H4/D1 first-slice experiment that writes deterministic CSV input for the existing canonical importer. Shared-bankroll portfolio selection profiles SHALL use only downloaded public OHLCV-derived entry-time values plus configured cost settings and SHALL NOT request private or live data.

#### Scenario: Approved public crypto data is requested
- **WHEN** a research runner requests historical crypto data for an approved symbol, timeframe, and UTC start/end
- **THEN** the downloader uses public unauthenticated market-data endpoints only
- **AND** writes deterministic local CSV artifacts and manifest metadata
- **AND** records provider, symbol, timeframe, requested range, received range, row counts, and any feed gaps
- **AND** cost-feasibility selection, when enabled by a portfolio runner, uses only downloaded public OHLCV-derived entry-time values plus configured cost settings and does not request private or live data.
