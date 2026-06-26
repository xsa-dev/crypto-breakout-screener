# breakout-backtesting-reporting Specification Delta

## ADDED Requirements
### Requirement: Backtests export forward-path diagnostics
Backtest report export SHALL support deterministic forward-path diagnostics for completed trades. These diagnostics SHALL be computed after trade creation and SHALL NOT alter entry selection, sizing, exits, risk controls, or reported realized metrics.

#### Scenario: Forward-path diagnostics are enabled
- **WHEN** a completed backtest report is exported with forward-path diagnostics enabled
- **THEN** exported artifacts include a forward-path diagnostics CSV with one row per trade and fixed M15 horizons 1, 2, 4, 8, and 16 bars when available
- **AND** each row records entry identity, current realized outcome, forward close return, MFE, MAE, time-to-MFE, time-to-MAE, breakout-level return flag, below-entry crossing flag, and unavailable horizon reason when applicable
- **AND** enabling the diagnostics does not change the exported trade list or realized metrics

### Requirement: Holding-horizon summaries are diagnostic-only
Backtest report export SHALL support deterministic synthetic holding-horizon summaries for fixed M15 horizons. These summaries SHALL be labeled as diagnostics and SHALL remain separate from actual realized backtest results.

#### Scenario: Holding-horizon summary is exported
- **WHEN** forward-path diagnostics are enabled for a completed backtest
- **THEN** exported artifacts include a holding-horizon summary CSV grouped by fixed horizon
- **AND** the summary reports trade count, unavailable count, synthetic net PnL, average forward return, average MFE, average MAE, and positive-forward-return ratio
- **AND** the actual backtest metrics remain based on the implemented trade lifecycle, not the synthetic horizons

### Requirement: Batch summaries compare passed and failed forward-path behavior
The BTCUSDT batch runner SHALL support opt-in forward-path diagnostic summaries that compare passed and failed windows without changing the batch verdict logic.

#### Scenario: Forward-path batch diagnostics are enabled
- **WHEN** the BTCUSDT quarterly batch completes with forward-path diagnostics enabled
- **THEN** the batch artifact directory includes `forward-path-window-summary.csv` and `passed-vs-failed-forward-path-summary.csv`
- **AND** the batch summary JSON references those diagnostic artifact paths
- **AND** the batch verdict fields `technical_pass` and `hypothesis_supported` remain based on the existing research thresholds
