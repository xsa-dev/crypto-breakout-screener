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

