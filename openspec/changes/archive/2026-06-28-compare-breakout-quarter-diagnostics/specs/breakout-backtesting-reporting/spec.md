## ADDED Requirements

### Requirement: Portfolio scorecards expose quarter diagnostics
The shared-bankroll portfolio report SHALL write deterministic quarter diagnostics that explain passing, failed, blocked, and unknown windows without changing trading behavior.

#### Scenario: Quarter diagnostics are written
- **WHEN** a portfolio smoke or promoted scorecard is generated
- **THEN** the artifacts include per-quarter diagnostics for status, blockers, trade counts, skipped signal counts, net profit, profit factor, max drawdown, regime contribution, BTC/ETH context, market breadth, and relative strength summaries
- **AND** the summary JSON links to the diagnostics artifact.

#### Scenario: Passing and failing windows are compared
- **WHEN** the run contains at least two comparable window statuses
- **THEN** the diagnostics summary compares passing windows against failed or blocked windows
- **AND** reports the strongest observed differences and unavailable fields.

#### Scenario: Diagnostics remain non-causal
- **WHEN** diagnostics include realized outcome metrics
- **THEN** those metrics are labeled as outcome analysis
- **AND** they are not used as entry-time selection inputs by this change.
