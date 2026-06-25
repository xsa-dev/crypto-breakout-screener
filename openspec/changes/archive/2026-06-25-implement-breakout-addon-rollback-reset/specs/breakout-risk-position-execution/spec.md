# breakout-risk-position-execution Specification

## MODIFIED Requirements
### Requirement: Add-ons are risk-budgeted
The system SHALL allow add-ons only on new local-extremum breakouts, cascade-level breakouts, or valid retests. Add-ons SHALL be 10%-20% of position by default, no more than two, and SHALL NOT exceed remaining trade risk budget or degrade average price beyond configured limits. When price rolls back to an add-on level, local risk logic SHALL produce a deterministic broker-neutral reset/reduction decision with a machine-readable reason and remaining base position state.

#### Scenario: Add-on is approved
- **WHEN** a valid add-on trigger occurs and remaining risk budget is sufficient
- **THEN** Risk Manager may approve an add-on within configured share bounds

#### Scenario: Add-on worsens average too much
- **WHEN** proposed add-on would degrade average price beyond `degrade_avg_price_limit_atr`
- **THEN** Risk Manager rejects the add-on

#### Scenario: Price rolls back to add-on level
- **WHEN** price rolls back to the add-on level after an add-on
- **THEN** the system exits or reduces the added portion according to configured rules
- **AND** the decision trace records `addon_level_rollback` and remaining base position state

#### Scenario: Price holds away from add-on level
- **WHEN** price remains away from the add-on level after an add-on
- **THEN** the system holds the added portion
- **AND** the decision trace records `addon_level_intact`
