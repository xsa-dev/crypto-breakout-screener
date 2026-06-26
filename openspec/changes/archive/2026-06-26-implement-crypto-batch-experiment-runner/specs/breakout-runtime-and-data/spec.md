## ADDED Requirements
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
