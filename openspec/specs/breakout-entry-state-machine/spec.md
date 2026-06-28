# breakout-entry-state-machine Specification

## Purpose
Define the breakout strategy lifecycle, entry-mode selection, breakout/retest/false-breakout decisions, and auditable state transitions used by downstream risk and execution components.
## Requirements
### Requirement: Entry engine supports three entry modes
The system SHALL support pre-entry, at-level entry, and post-breakout entry modes with default base-position shares of 30%, 30%, and 40% respectively.

#### Scenario: Pre-entry is eligible
- **WHEN** `score_pre_entry` meets threshold and slow approach plus consolidation/protorgovka are present before the level
- **THEN** the system may create a pre-entry intent for at most the configured pre-entry share

#### Scenario: Pre-entry cannot take full size
- **WHEN** the system creates a pre-entry intent before confirmed breakout
- **THEN** the intent size is capped by `pre_entry_share`
- **AND** the system does not allow the full planned position to be entered before breakout confirmation

#### Scenario: At-level entry is eligible
- **WHEN** price touches the level or eats density at the level with confirmed activity
- **THEN** the system may create an at-level entry intent for at most the configured at-level share

#### Scenario: Upper protorgovka boundary is broken with density eating
- **WHEN** price breaks the upper boundary of the pre-level protorgovka and market activity indicates density eating at or near the level
- **THEN** the system may create an at-level or breakout-entry intent according to configuration

#### Scenario: Lower protorgovka boundary entry is enabled
- **WHEN** price is near the lower boundary of protorgovka before an expected upper-boundary breakout
- **THEN** the system may create that rare early long-entry intent only when an explicit configuration flag enables this entry subtype

#### Scenario: Post-breakout entry is eligible
- **WHEN** price closes or ticks beyond `level + breakout_buffer` for long or below symmetric short threshold and score passes threshold
- **THEN** the system may create a post-breakout entry intent for at most the configured post-breakout share

#### Scenario: Entry share caps are enforced
- **WHEN** multiple entry modes are eligible for one setup
- **THEN** each generated intent is capped by its configured share
- **AND** cumulative planned exposure cannot exceed the configured base position

### Requirement: Protorgovka range is configurable
The system SHALL represent the PDF-specific pre-level protorgovka range as `protorgovka_range_percent` with a default accepted range of 0.3% to 2.0% unless overridden by instrument-specific configuration.

#### Scenario: Protorgovka range is valid
- **WHEN** pre-level consolidation/protorgovka forms within the configured 0.3% to 2.0% range
- **THEN** the setup evaluator may treat it as valid protorgovka input for pre-entry and at-level entry scenarios

#### Scenario: Protorgovka range is outside limits
- **WHEN** pre-level consolidation/protorgovka is narrower or wider than configured limits
- **THEN** the setup evaluator records the reason and does not award full protorgovka credit

### Requirement: Breakout confirmation is formalized
The system SHALL confirm long breakouts using `(close_or_tick_price > level + breakout_buffer) AND (score >= score_threshold) AND optional trend filter passes`, with symmetric short logic.

#### Scenario: Long breakout confirmed
- **WHEN** price is above the level plus buffer, score meets threshold, and trend filter passes when enabled
- **THEN** the system transitions to breakout confirmation logic for a long setup

#### Scenario: Confirmation fails
- **WHEN** any required confirmation component fails
- **THEN** the system does not treat the move as a confirmed breakout

### Requirement: Retest is a first-class lifecycle scenario
The system SHALL monitor retest after confirmed breakout. A retest is valid only when price returns to `level ± retest_tolerance`, does not break breakout structure, holds the level side-symmetrically, and forms a micro-impulse in the trade direction. Long retests SHALL hold at or above the level; short retests SHALL hold at or below the level.

#### Scenario: Long retest holds
- **WHEN** long price returns to the retest zone, holds at or above the level, and micro-impulse resumes in direction
- **THEN** the system may allow add-on review and stop adjustment according to risk rules

#### Scenario: Short retest holds
- **WHEN** short price returns to the retest zone, holds at or below the level, and micro-impulse resumes in direction
- **THEN** the system may allow add-on review and stop adjustment according to risk rules

#### Scenario: Retest fails
- **WHEN** price returns through the level, does not hold structure for the setup side, or lacks a directional micro-impulse
- **THEN** the system transitions to false-breakout handling

### Requirement: False breakout is detected explicitly
The system SHALL detect false breakout as a strategy state, not only as a stop-loss result. For long, false breakout occurs when price breaks upward but within `false_breakout_max_bars` returns under the level, closes below `level - false_breakout_buffer`, loses structure such as Lower High, or fails retest; symmetric short logic applies.

#### Scenario: Long false breakout
- **WHEN** a long breakout returns below the level within the configured max bars and loses structure
- **THEN** the system closes or rejects the long according to execution mode
- **AND** reversal is allowed only when `allow_reversal_on_false_breakout=true`

### Requirement: Required finite state machine is preserved
The system SHALL implement the states `LEVEL_SEARCH`, `SETUP_READY`, `SCENARIO_PICK`, `ENTRY_MODE_PICK`, `POSITION_OPEN`, `BREAKOUT_CONFIRM`, `RETEST_MONITOR`, `ADDON_MONITOR`, `PARTIAL_EXIT`, `FALSE_BREAKOUT`, and `COMPLETE` as stable machine-readable states with transition reason logging.

#### Scenario: Normal breakout lifecycle
- **WHEN** a valid level, setup, scenario, entry, confirmation, retest/add-on, and exit sequence occurs
- **THEN** the state machine records transitions from level search through complete without skipping required decision states

#### Scenario: Setup breaks down
- **WHEN** a setup becomes invalid before entry
- **THEN** the state machine returns to `LEVEL_SEARCH` with a reason code

#### Scenario: Transition history is testable
- **WHEN** a setup progresses through entry, confirmation, retest/add-on review, and exit
- **THEN** tests can assert the ordered state transition history and reasons

### Requirement: Long and short strategy rules are symmetric unless configured otherwise
The system SHALL support long and short versions of level/setup/entry/confirmation/retest/false-breakout/risk rules. Exceptions such as `fast_exit_for_low_breakouts` SHALL be explicit configuration rather than hidden asymmetry.

#### Scenario: Short breakout is evaluated
- **WHEN** price breaks below a valid support level with score and context filters passing
- **THEN** the system evaluates the short setup through the same state machine and risk gates with side-symmetric thresholds

#### Scenario: Asymmetric low-breakout exit is configured
- **WHEN** `fast_exit_for_low_breakouts` is enabled
- **THEN** the system applies the faster low-breakout exit behavior and records that configured asymmetry in the decision trace

### Requirement: Lower protorgovka early entry remains explicitly gated
The system SHALL create the rare lower-protorgovka boundary early long-entry intent only when `lower_protorgovka_entry_enabled` is explicitly enabled, the caller marks the lower-protorgovka condition ready, the setup side is long, and normal score/base-quantity gates pass. When any of those conditions is absent, generated entry intents SHALL remain unchanged and SHALL NOT include the lower-protorgovka subtype.

#### Scenario: Lower protorgovka early entry is enabled
- **WHEN** `lower_protorgovka_entry_enabled=true`, `lower_protorgovka_ready=true`, side is long, score passes, and base quantity is positive
- **THEN** the entry engine creates a pre-entry intent capped by `pre_entry_share`
- **AND** the intent records `lower_protorgovka_boundary` metadata for auditability

#### Scenario: Lower protorgovka early entry is not explicitly enabled
- **WHEN** the flag is disabled, readiness is false, side is short, score is blocked, or base quantity is not positive
- **THEN** the entry engine does not create a lower-protorgovka intent

### Requirement: Breakout candidates expose lifecycle state audit
The breakout research runner SHALL expose deterministic lifecycle state evidence for accepted and skipped candidates.

#### Scenario: Candidate reaches lifecycle states
- **WHEN** a breakout candidate is evaluated
- **THEN** artifacts record which ordered states were reached among `level_found`, `compression`, `approach`, `breakout`, `confirmation`, `retest`, `continuation`, and `failure_exit`
- **AND** the state evidence is derived only from data available up to the relevant state timestamp.

#### Scenario: Candidate is skipped
- **WHEN** a candidate is skipped by a filter, regime, selection gate, or exposure rule
- **THEN** the candidate remains in audit artifacts
- **AND** its furthest lifecycle state and machine-readable blocker are preserved.

#### Scenario: Lifecycle counts are reported
- **WHEN** portfolio reports are written
- **THEN** summary artifacts include lifecycle state counts by window and, when available, by regime.

