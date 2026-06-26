## ADDED Requirements
### Requirement: Crypto batch experiment runner summarizes multiple BTCUSDT windows
The system SHALL provide a local research batch runner for BTCUSDT crypto historical experiments that executes multiple explicit historical windows through the existing public-data download and M15 backtest path, then writes deterministic batch summary artifacts.

#### Scenario: Batch runner executes multiple windows
- **WHEN** the user runs the BTCUSDT batch experiment command with explicit windows or an approved preset
- **THEN** the runner evaluates each window using public unauthenticated BTCUSDT M15/H1/H4/D1 data
- **AND** runs the existing M15 crypto experiment path for each completed window
- **AND** writes per-window report artifacts and dataset manifests
- **AND** writes batch summary CSV and JSON artifacts under an ignored local artifact directory

#### Scenario: Batch summary contains per-window metrics
- **WHEN** a batch completes
- **THEN** each summary row includes window label, start, end, status, blocker or error reason when applicable, run id, dataset hash, config hash, bar count, trade count, net profit, max drawdown, profit factor, win rate, Sharpe ratio, average trade or expectancy, feed gap count, context timeframe availability, downloaded CSV paths, manifest path, and artifact directory

#### Scenario: Batch output is reproducible for equivalent inputs
- **WHEN** the batch runner is executed twice with the same windows, provider responses or fixture inputs, costs, config, and random seed
- **THEN** per-window dataset hashes, config hashes, run ids, deterministic report artifacts, and batch summary rows match except for explicitly generated-at metadata

### Requirement: Crypto batch research verdict is conservative and non-production
The batch runner SHALL produce a research-only verdict that distinguishes technical pipeline success from trading-hypothesis support. It SHALL NOT claim production readiness, OOS approval, full-auto readiness, or live trading permission.

#### Scenario: All windows satisfy research thresholds
- **WHEN** all required windows complete without feed gaps, include required metrics, have at least one trade, and satisfy configured research thresholds
- **THEN** the summary marks `technical_pass` true
- **AND** marks the hypothesis as supported for research screening only
- **AND** records the thresholds used

#### Scenario: Any required window fails or violates thresholds
- **WHEN** any required window fails to download, fails to backtest, has feed gaps, has no trades, lacks required metrics, or violates configured research thresholds
- **THEN** the summary marks the hypothesis as not supported
- **AND** records machine-readable blocker reasons per failed window
- **AND** does not mark the batch as production-approved

#### Scenario: Batch result is reviewed
- **WHEN** a user inspects the batch summary
- **THEN** the output clearly states that the result is a research screen only and not production OOS/full-auto approval
