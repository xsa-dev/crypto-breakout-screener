# breakout-backtesting-reporting Specification

## Purpose
Define deterministic local replay, validation analysis, and reproducible report artifacts for the breakout strategy before any live-trading approval.
## Requirements
### Requirement: Backtesting uses deterministic data and configuration hashes
The system SHALL produce deterministic backtest results for the same dataset hash and config hash, subject only to explicitly seeded randomness.

#### Scenario: Same run is repeated
- **WHEN** a backtest is rerun with identical dataset hash, config hash, and random seed
- **THEN** signals, trades, and metrics match the previous run

### Requirement: Backtests include realistic trading costs
The system SHALL model spread, commission, slippage, and funding/swap where applicable for the tested market.

#### Scenario: Cost model is missing
- **WHEN** a backtest is requested without required cost assumptions
- **THEN** the system blocks the run or marks it as non-acceptance research output

### Requirement: Validation separates IS, OOS, walk-forward, and Monte Carlo
The system SHALL support in-sample optimization, out-of-sample validation, walk-forward evaluation, and Monte Carlo robustness analysis.

#### Scenario: Optimization is requested
- **WHEN** parameters are optimized
- **THEN** optimization occurs only inside configured in-sample windows

#### Scenario: Walk-forward is run
- **WHEN** walk-forward validation is configured
- **THEN** the system reports train/validate/forward windows and pass ratio

#### Scenario: Monte Carlo is run
- **WHEN** Monte Carlo analysis is configured
- **THEN** the system can perturb trade order, slippage, trade skipping, or price path according to configured methods

### Requirement: Required metrics are reported
The system SHALL report CAGR, Sharpe Ratio, Max Drawdown, Win Rate, Expectancy, Average Trade, Avg Holding Time, and OOS Performance. It SHOULD also report Profit Factor and Exposure.

#### Scenario: Backtest report generated
- **WHEN** a backtest completes
- **THEN** the report includes all required metrics or explicit unavailable reasons

### Requirement: Reports include strategy diagnostics
The system SHALL produce reports with equity curve, drawdown chart, distribution of returns, trade list, scenario breakdown, score distribution, false breakout analysis, slippage report, parameter snapshot, and CSV/Parquet export.

#### Scenario: Report is exported
- **WHEN** the user exports a completed run report
- **THEN** exported artifacts include metrics, charts/series data, trade list, scenario/score diagnostics, and parameter snapshot

### Requirement: Production OOS thresholds are explicit gates
The system SHALL require project-specific numeric OOS/business-validity thresholds before any production full-auto GO. If thresholds are not configured, production full-auto approval is blocked even when backtest artifacts exist.

#### Scenario: OOS thresholds are missing
- **WHEN** a release candidate requests production full-auto approval without configured OOS thresholds
- **THEN** the review blocks production full-auto GO and records the missing thresholds

#### Scenario: OOS thresholds are configured
- **WHEN** OOS thresholds are configured for the target market and broker scope
- **THEN** acceptance review compares backtest/walk-forward/OOS outputs against those thresholds

### Requirement: Acceptance gates are measurable
The system SHALL require acceptance gates for functional coverage, determinism, risk limits, reconnect/idempotency, logs, test artifacts, documentation, operations, and OOS business validity.

#### Scenario: Acceptance review runs
- **WHEN** a release candidate is reviewed
- **THEN** the review can verify each acceptance category with concrete artifacts or explicit blockers

### Requirement: Backtests use the online information boundary
The backtest engine SHALL evaluate historical bars/ticks using only information available at each simulated timestamp and SHALL reuse the same level/setup/state/risk logic as online evaluation.

#### Scenario: Future data is unavailable during simulation
- **WHEN** a backtest evaluates a signal at bar N
- **THEN** the strategy cannot inspect bars after N except for explicitly delayed confirmation that would also be unavailable live

### Requirement: Reports are reproducible artifacts
The reporting layer SHALL produce deterministic report artifacts with config hash, dataset hash, parameter snapshot, trade list, scenario breakdown, score distribution, false-breakout analysis, slippage assumptions, equity, drawdown, and return distribution. Local report export SHALL materialize these diagnostics as separate deterministic artifacts, or record explicit unavailable reasons for unsupported optional formats.

#### Scenario: Report links to run metadata
- **WHEN** a backtest report is generated
- **THEN** it includes or references the backtest run id, config hash, dataset hash, time range, and exported artifact paths

#### Scenario: Diagnostic artifacts are exported
- **WHEN** a completed report is exported locally
- **THEN** artifact paths include the full report, trade list, equity curve, drawdown curve, return distribution, metrics, scenario breakdown, score distribution, false-breakout analysis, slippage report, and parameter snapshot
- **AND** repeated exports of the same report produce stable artifact names and content

### Requirement: Crypto experiment runner produces deterministic local backtest artifacts
The system SHALL provide a simple local runner or CLI/script entrypoint for the first BTCUSDT crypto historical experiment. The runner SHALL load normalized historical bars, compute dataset and configuration hashes, run the existing deterministic backtest engine, export report artifacts, write the dataset manifest, and print a concise summary. The runner SHALL also support a public download flow that writes BTCUSDT M15/H1/H4/D1 public historical OHLCV CSV input before running or preparing the existing experiment path.

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

#### Scenario: Runner downloads public BTCUSDT data before running
- **WHEN** the user runs the crypto experiment command in public-download mode with BTCUSDT, M15/H1/H4/D1, and explicit UTC start/end timestamps
- **THEN** the command downloads public unauthenticated OHLCV/kline data for all four required timeframes
- **AND** writes deterministic CSV inputs under an ignored local artifact/data directory
- **AND** runs or can immediately run the existing importer/backtest path against the M15 CSV while retaining H1/H4/D1 CSV paths as context datasets
- **AND** prints or records both the downloaded CSV paths and the report/manifest artifact path when a backtest is run

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

### Requirement: Production OOS approval gate is fail-closed
The system SHALL provide a deterministic local approval gate for production OOS/business-validity review that compares completed backtest metrics against explicit configured thresholds. The gate SHALL block approval when thresholds are absent, when a configured metric is missing or unavailable, or when a configured threshold is not met. Passing this local gate SHALL NOT enable live broker execution or production `full_auto` unless separately approved by deferred-scope gates.

#### Scenario: Thresholds are missing
- **WHEN** production OOS approval is evaluated without any configured numeric thresholds
- **THEN** the gate blocks approval
- **AND** the decision records `missing_oos_thresholds`

#### Scenario: Configured thresholds pass
- **WHEN** production OOS approval is evaluated with configured thresholds that are all satisfied by report metrics
- **THEN** the gate returns an approved local decision
- **AND** checked metrics are recorded for audit

#### Scenario: Configured metric is missing, unavailable, or fails
- **WHEN** a configured threshold references a missing metric, a metric with an unavailable reason, a `None` metric value, or a value that does not satisfy the threshold
- **THEN** the gate blocks approval
- **AND** the decision records a machine-readable blocker for that metric

### Requirement: Public download failures do not create completed reports
Public data download failures SHALL fail explicitly and SHALL NOT feed partial or malformed data into the backtest runner as a completed dataset.

#### Scenario: Provider returns an error, timeout, empty result, or malformed payload
- **WHEN** the public downloader cannot retrieve a valid non-empty BTCUSDT M15/H1/H4/D1 OHLCV datasets for the requested range
- **THEN** the command fails with an explicit error
- **AND** no completed report artifact is claimed for that failed download

#### Scenario: Provider pagination is rate-limited or retried
- **WHEN** the public provider temporarily rate-limits or fails a page request
- **THEN** the downloader may retry with bounded backoff
- **AND** it eventually succeeds deterministically or fails with a clear bounded-retry error
