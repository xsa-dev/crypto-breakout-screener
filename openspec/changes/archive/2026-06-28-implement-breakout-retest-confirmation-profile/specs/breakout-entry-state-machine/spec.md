## ADDED Requirements

### Requirement: Breakout entry can require confirmation and retest
The breakout entry state machine SHALL support an opt-in profile that blocks or delays candidates until configured confirmation and retest evidence exists.

#### Scenario: Confirmation is missing
- **WHEN** a confirmation-aware profile evaluates a breakout candidate without required close/tick confirmation beyond the configured level and buffer
- **THEN** the candidate is retained with blocker `portfolio_selection_confirmation_missing`
- **AND** it does not consume exposure or affect PnL.

#### Scenario: Required retest is missing
- **WHEN** retest mode is enabled and no valid retest occurs within the configured decision window
- **THEN** the candidate is retained with blocker `portfolio_selection_retest_missing`.

#### Scenario: Retest fails
- **WHEN** price retests but fails structure or continuation criteria
- **THEN** the candidate is retained or exited with `portfolio_selection_retest_failed`
- **AND** the decision uses only data available through the retest decision horizon.

#### Scenario: Retest decisions are reported
- **WHEN** portfolio artifacts are written
- **THEN** confirmation and retest pass/missing/failed counts are reported by quarter and, when available, by regime.
