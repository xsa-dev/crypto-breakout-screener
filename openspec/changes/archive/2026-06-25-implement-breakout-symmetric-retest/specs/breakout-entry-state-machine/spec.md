## MODIFIED Requirements
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

### Requirement: Long and short strategy rules are symmetric unless configured otherwise
The system SHALL support long and short versions of level/setup/entry/confirmation/retest/false-breakout/risk rules. Exceptions such as `fast_exit_for_low_breakouts` SHALL be explicit configuration rather than hidden asymmetry.

#### Scenario: Short breakout is evaluated
- **WHEN** price breaks below a valid support level with score and context filters passing
- **THEN** the system evaluates the short setup through the same state machine and risk gates with side-symmetric thresholds

#### Scenario: Asymmetric low-breakout exit is configured
- **WHEN** `fast_exit_for_low_breakouts` is enabled
- **THEN** the system applies the faster low-breakout exit behavior and records that configured asymmetry in the decision trace
