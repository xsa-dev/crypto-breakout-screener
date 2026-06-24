## MODIFIED Requirements

### Requirement: Operation modes are explicit and staged
The system SHALL implement typed local configuration for `advisory_only`, `semi_auto`, and `full_auto` operation modes while keeping live `full_auto` execution blocked by deferred-scope gates until a later approved execution change.

#### Scenario: Baseline mode is safe
- **WHEN** the baseline breakout configuration is loaded during this foundation slice
- **THEN** the operation mode defaults to `semi_auto`
- **AND** no broker order can be submitted by foundation components

### Requirement: Market data providers expose bars, ticks, and optional order book
The system SHALL expose local provider protocols/interfaces for historical bars, recent or streaming ticks, and optional order-book/density data using canonical DTOs that can be implemented by fakes in tests before any live adapter is approved.

#### Scenario: Fake provider is sufficient for tests
- **WHEN** foundation tests evaluate breakout levels or setup scores
- **THEN** they can use an in-memory provider without network credentials
- **AND** the provider returns canonical bars/ticks accepted by the normalizer

### Requirement: Data normalization prevents inconsistent inputs
The normalizer SHALL implement UTC conversion, deterministic deduplication, ordering validation, configured resampling/gap marking, and metadata propagation for canonical bars and ticks.

#### Scenario: Out-of-order input is normalized or rejected
- **WHEN** provider data arrives out of timestamp order
- **THEN** the normalizer emits deterministic ordered events or raises an explicit validation error according to configuration

### Requirement: No-lookahead invariant is enforced
The foundation implementation SHALL include tests proving online calculations do not use future bars, future ticks, or unconfirmed pivot right-window bars.

#### Scenario: Closed-bar-only signal calculation is tested
- **WHEN** an online setup is evaluated at a historical bar
- **THEN** tests verify only closed bars available at that timestamp are passed to level and setup calculations
