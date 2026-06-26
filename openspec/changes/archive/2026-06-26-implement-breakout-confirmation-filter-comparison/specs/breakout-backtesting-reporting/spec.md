# breakout-backtesting-reporting Specification Delta

## ADDED Requirements
### Requirement: Backtests compare fixed breakout-confirmation profiles
The batch research runner SHALL support fixed, named breakout-confirmation comparison profiles for BTCUSDT public-data research.

#### Scenario: Confirmation profile is selected
- **WHEN** a batch run selects a supported confirmation profile
- **THEN** every window summary records `confirmation_filter_profile`
- **AND** every window summary records `confirmation_filter_settings_json`
- **AND** every window summary records `confirmation_filter_skip_counts_json`
- **AND** the batch JSON summary records the selected confirmation profile separately from gate, feature, and risk-control profiles.

#### Scenario: Confirmation profile is disabled
- **WHEN** the reference profile runs without confirmation filters
- **THEN** confirmation settings are empty or disabled
- **AND** confirmation skip counts are empty
- **AND** reference behavior is preserved.

### Requirement: Confirmation comparison reports research verdicts
Confirmation comparison artifacts SHALL make it possible to compare each fixed profile against the reference profile.

#### Scenario: Quarterly comparison is completed
- **WHEN** quarterly 2023-2024 BTCUSDT batches finish for confirmation profiles
- **THEN** the report states passed window count, failed window count, total trade count, total net profit, worst max drawdown, and `hypothesis_supported`
- **AND** remaining failed windows list blockers
- **AND** the report states whether confirmation improved, supported, or failed to support the breakout hypothesis.
