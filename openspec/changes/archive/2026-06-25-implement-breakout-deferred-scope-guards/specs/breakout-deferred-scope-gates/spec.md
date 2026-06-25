## MODIFIED Requirements

### Requirement: Full-auto mode remains non-production until separately approved
The system SHALL define `full_auto` as a supported mode contract, but production full-auto enablement SHALL remain blocked until a separate OpenSpec change defines production readiness gates, OOS thresholds, risk approvals, operator controls, rollback policy, and live-execution adapter scope. Local configuration validation SHALL fail closed for `full_auto` by default; any pre-approval opt-in SHALL be named as contract-validation-only rather than production approval.

#### Scenario: Config enables production full-auto before approval
- **WHEN** configuration attempts to enable production `full_auto` before a full-auto approval change exists
- **THEN** startup or mode activation is blocked with an explicit reason
- **AND** the reason identifies that a dedicated full-auto OpenSpec change is required

#### Scenario: Full-auto is used in tests
- **WHEN** tests exercise `full_auto` state transitions with fake adapters and no live side effects
- **THEN** the behavior is allowed as contract validation, not production approval
- **AND** the test must opt in through the explicit local contract-validation-only guard rather than changing the default production-safe behavior
