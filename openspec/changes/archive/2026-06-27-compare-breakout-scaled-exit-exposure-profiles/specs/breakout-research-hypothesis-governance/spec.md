# breakout-research-hypothesis-governance Specification Delta

## MODIFIED Requirements
### Requirement: BTCUSDT research uses an eight-quarter scorecard
The system SHALL require every selected BTCUSDT breakout research hypothesis to define an explicit eight-quarter scorecard before source implementation. For this research line, `8/8` means all eight quarterly windows from 2023q1 through 2024q4 pass configured research thresholds.

#### Scenario: Exposure-scaled profile scorecard is created
- **WHEN** an exposure-scaled exit/path-risk profile is selected
- **THEN** the scorecard contains exactly these windows: `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, and `2024q4`
- **AND** each quarter has one of the statuses `pass`, `fail`, `unknown`, or `blocked`
- **AND** each quarter identifies the command, artifact, metric, blocker, or review evidence needed to verify it
- **AND** changing fixed candidate exposure SHALL NOT weaken `min_trade_count`, `min_net_profit`, `min_profit_factor`, `min_max_drawdown`, feed-gap requirements, realistic-cost requirements, or quarter coverage.
