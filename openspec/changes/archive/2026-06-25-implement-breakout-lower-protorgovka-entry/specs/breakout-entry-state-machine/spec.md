# breakout-entry-state-machine Specification

## ADDED Requirements
### Requirement: Lower protorgovka early entry remains explicitly gated
The system SHALL create the rare lower-protorgovka boundary early long-entry intent only when `lower_protorgovka_entry_enabled` is explicitly enabled, the caller marks the lower-protorgovka condition ready, the setup side is long, and normal score/base-quantity gates pass. When any of those conditions is absent, generated entry intents SHALL remain unchanged and SHALL NOT include the lower-protorgovka subtype.

#### Scenario: Lower protorgovka early entry is enabled
- **WHEN** `lower_protorgovka_entry_enabled=true`, `lower_protorgovka_ready=true`, side is long, score passes, and base quantity is positive
- **THEN** the entry engine creates a pre-entry intent capped by `pre_entry_share`
- **AND** the intent records `lower_protorgovka_boundary` metadata for auditability

#### Scenario: Lower protorgovka early entry is not explicitly enabled
- **WHEN** the flag is disabled, readiness is false, side is short, score is blocked, or base quantity is not positive
- **THEN** the entry engine does not create a lower-protorgovka intent
