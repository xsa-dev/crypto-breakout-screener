## MODIFIED Requirements

### Requirement: Required finite state machine is preserved
The system SHALL implement the states `LEVEL_SEARCH`, `SETUP_READY`, `SCENARIO_PICK`, `ENTRY_MODE_PICK`, `POSITION_OPEN`, `BREAKOUT_CONFIRM`, `RETEST_MONITOR`, `ADDON_MONITOR`, `PARTIAL_EXIT`, `FALSE_BREAKOUT`, and `COMPLETE` as stable machine-readable states with transition reason logging.

#### Scenario: Transition history is testable
- **WHEN** a setup progresses through entry, confirmation, retest/add-on review, and exit
- **THEN** tests can assert the ordered state transition history and reasons

### Requirement: Entry engine supports three entry modes
The system SHALL implement entry-intent generation for pre-entry, at-level, and post-breakout modes with default base-position share caps of 30%, 30%, and 40%.

#### Scenario: Entry share caps are enforced
- **WHEN** multiple entry modes are eligible for one setup
- **THEN** each generated intent is capped by its configured share
- **AND** cumulative planned exposure cannot exceed the configured base position
