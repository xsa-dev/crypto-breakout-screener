# breakout-backtesting-reporting Specification Delta

## ADDED Requirements
### Requirement: Backtests compare fixed volatility-regime filter profiles
The batch research runner SHALL support fixed, named volatility/no-trade regime filter profiles for BTCUSDT breakout research while preserving the existing baseline/reference profiles.

#### Scenario: Required volatility-regime profiles are available
- **WHEN** the quarterly BTCUSDT batch runner is invoked with each required volatility-regime profile
- **THEN** it runs the profile over the requested windows
- **AND** it records the profile name, settings, skip counts, artifact paths, and per-window blockers in summary CSV/JSON
- **AND** it keeps lifecycle gates, M15-slope feature filtering, and max-trades risk control identical to the approved reference profile except for the named regime filter condition

#### Scenario: Volatility-regime comparison completes
- **WHEN** all required volatility-regime profiles complete over quarterly 2023-2024 windows
- **THEN** the aggregate summary reports passed window count, failed window count, total trade count, total net profit, worst max drawdown, mean profit factor, hypothesis_supported, and hypothesis_not_supported for each profile
- **AND** the result is not represented as production approval

### Requirement: Regime-filter reporting is separate from gate and risk reporting
The batch summary SHALL expose volatility/no-trade regime filter reporting separately from lifecycle gates, feature filters, and risk controls.

#### Scenario: Summary CSV is written
- **WHEN** a volatility-regime profile is run
- **THEN** the summary CSV includes `regime_filter_profile`, `regime_filter_settings_json`, and `regime_filter_skip_counts_json`
- **AND** existing `gate_profile`, `feature_filter_profile`, and `risk_control_profile` fields remain populated according to their existing meanings

#### Scenario: Summary JSON is written
- **WHEN** a volatility-regime profile is run
- **THEN** the summary JSON includes the same regime-filter profile, settings, and skip-count data as the CSV
