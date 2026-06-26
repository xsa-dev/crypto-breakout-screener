# breakout-backtesting-reporting Specification Delta

## ADDED Requirements
### Requirement: Backtests export failed-window bad-regime diagnostics
The backtest research reporting layer SHALL support deterministic diagnostics for failed windows of a selected research profile without changing default backtest behavior.

#### Scenario: Diagnostics enabled for failed quarterly windows
- **WHEN** diagnostics are enabled for `conservative-v1-m15-slope-positive-max-trades-8` over quarterly BTCUSDT 2023-2024 windows
- **THEN** failed-window diagnostic artifacts are written for windows that do not pass research thresholds
- **AND** each artifact includes profile name, window label, run id, and artifact schema metadata
- **AND** default runs without diagnostics do not require the additional artifacts

### Requirement: Bad-regime diagnostics report traceable bucket evidence
Bad-regime diagnostics SHALL aggregate failed-window evidence by deterministic dimensions derived from existing run artifacts and entry/context features.

#### Scenario: Bucket diagnostics are generated
- **WHEN** a failed window has entry feature snapshots and trades available
- **THEN** diagnostics include bucket-level trade count, net PnL, and available adverse/drawdown metrics
- **AND** buckets are stable across repeated runs on the same inputs
- **AND** bucket definitions are documented in the artifact or companion metadata

### Requirement: Worst drawdown runs are reportable
Failed-window diagnostics SHALL identify drawdown runs or worst-day clusters sufficient to explain whether a failure is broad-based or concentrated.

#### Scenario: Drawdown failure is concentrated
- **WHEN** a failed window breaches the max drawdown research threshold
- **THEN** diagnostics include the worst drawdown run or worst contributing day clusters where calculable
- **AND** output distinguishes profitable-but-drawdown-blocked windows from negative-expectancy windows
