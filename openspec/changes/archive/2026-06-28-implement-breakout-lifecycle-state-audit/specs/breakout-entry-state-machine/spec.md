## ADDED Requirements

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
