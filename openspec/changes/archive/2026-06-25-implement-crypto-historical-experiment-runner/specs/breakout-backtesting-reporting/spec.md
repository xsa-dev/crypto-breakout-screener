## ADDED Requirements
### Requirement: Crypto experiment runner produces deterministic local backtest artifacts
The system SHALL provide a simple local runner or CLI/script entrypoint for the first BTCUSDT crypto historical experiment. The runner SHALL load normalized historical bars, compute dataset and configuration hashes, run the existing deterministic backtest engine, export report artifacts, write the dataset manifest, and print a concise summary.

#### Scenario: Runner executes BTCUSDT fixture or public-data experiment
- **WHEN** the user runs the crypto historical experiment command with BTCUSDT M15 fixture or public historical data
- **THEN** the command loads and normalizes the data
- **AND** computes a dataset hash
- **AND** constructs an explicit `BacktestConfig`
- **AND** runs `BacktestEngine`
- **AND** exports the report artifacts and dataset manifest to a local run directory
- **AND** prints run id, symbol, timeframe, bar count, dataset hash, config hash, trade count, net PnL or equivalent total metric, max drawdown, win rate, and artifact paths

#### Scenario: Repeated runner execution is reproducible
- **WHEN** the runner is executed twice with the same normalized dataset, cost assumptions, config, and random seed
- **THEN** the dataset hash, config hash, run id, and deterministic report artifacts match

### Requirement: Crypto cost assumptions are explicit and research-scoped
The system SHALL require explicit non-zero crypto research cost assumptions for the first BTCUSDT perpetual/futures experiment, including spread, slippage, commission or fee, and funding assumption or an explicit unavailable/deferred reason.

#### Scenario: Crypto costs are configured
- **WHEN** the runner builds the backtest configuration for BTCUSDT perpetual/futures research
- **THEN** spread, slippage, and commission/fee assumptions are explicit and non-zero unless the run is marked non-acceptance research
- **AND** funding is either modeled explicitly or recorded as unavailable/deferred in report or manifest limitations

#### Scenario: Missing production-quality inputs are visible
- **WHEN** funding, higher-timeframe context, order-book density, or other production-quality inputs are unavailable for the first experiment
- **THEN** the report or manifest records explicit unavailable reasons
- **AND** the result is not represented as production full-auto or production OOS approval

### Requirement: Experiment artifacts include the dataset manifest
The report export path for crypto historical experiments SHALL include the existing deterministic backtest report artifacts and the dataset manifest in the same local artifact directory.

#### Scenario: Artifact directory is produced
- **WHEN** a crypto historical experiment completes
- **THEN** the artifact directory includes the full report JSON, trade list, equity curve, drawdown curve, return distribution, metrics, scenario breakdown, score distribution, false-breakout analysis, slippage report, parameter snapshot, and dataset manifest
- **AND** generated artifact directories are ignored or otherwise protected from accidental large local artifact commits unless a small fixture artifact is intentionally committed for tests
