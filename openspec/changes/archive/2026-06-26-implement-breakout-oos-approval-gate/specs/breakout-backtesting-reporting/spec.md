# breakout-backtesting-reporting Specification

## ADDED Requirements

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
