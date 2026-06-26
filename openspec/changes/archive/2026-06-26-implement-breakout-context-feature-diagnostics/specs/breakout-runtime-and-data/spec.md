## ADDED Requirements
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
