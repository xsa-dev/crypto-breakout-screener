## ADDED Requirements

### Requirement: Reports disclose Heikin-Ashi feature usage
Backtesting and portfolio reports SHALL disclose when Heikin-Ashi was used as a derived feature view.

#### Scenario: Report includes Heikin-Ashi features
- **WHEN** scorecards, feature snapshots, or diagnostics include Heikin-Ashi fields
- **THEN** the report states that Heikin-Ashi was used only for feature extraction
- **AND** links or records the raw OHLCV accounting artifacts.

#### Scenario: Raw accounting artifact is missing
- **WHEN** a report uses Heikin-Ashi features but lacks raw-price accounting evidence
- **THEN** the run is marked blocked or incomplete for economic conclusions.
