## MODIFIED Requirements

### Requirement: Crypto batch runner uses public unauthenticated BTCUSDT data only
The crypto batch experiment runner SHALL use only public unauthenticated market data for approved research symbols and SHALL preserve deterministic data boundaries for each window.

#### Scenario: Batch window data is loaded
- **WHEN** a batch window is evaluated for an approved crypto research symbol
- **THEN** the runner uses public unauthenticated OHLCV/kline input for that symbol
- **AND** downloads or reuses M15, H1, H4, and D1 datasets for the window
- **AND** uses M15 as the execution/backtest input
- **AND** records H1/H4/D1 as context datasets in per-window manifests and batch summaries
- **AND** records the selected symbol in every manifest and batch summary.

#### Scenario: BTCUSDT remains the default research symbol
- **WHEN** a user runs the crypto batch without an explicit symbol
- **THEN** the runner evaluates `BTCUSDT`
- **AND** existing BTCUSDT artifact path, summary, and verdict behavior remains unchanged.

#### Scenario: ETHUSDT and fixed altcoin universe symbols are approved
- **WHEN** a user requests `ETHUSDT` or another symbol from the fixed approved crypto research allowlist of 50 non-BTC altcoin candidates
- **THEN** the runner accepts the symbol for public-data historical research
- **AND** the run remains read-only, unauthenticated, local-artifact-only, and research-only.

#### Scenario: Fixed universe avoids dynamic replacement
- **WHEN** a symbol from the fixed approved allowlist has missing or unavailable public historical data
- **THEN** the runner records the symbol-specific blocker
- **AND** it does not silently replace the symbol with a different live top-market-cap or trending symbol.

#### Scenario: Unsupported batch scope is requested
- **WHEN** a user requests a symbol outside the fixed approved crypto research allowlist, non-crypto market, FX instrument, private data source, or open-ended window
- **THEN** the runner fails closed with an explicit validation error
- **AND** no completed batch summary claims the unsupported request passed.
