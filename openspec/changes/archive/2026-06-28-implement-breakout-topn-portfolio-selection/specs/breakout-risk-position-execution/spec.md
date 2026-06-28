## ADDED Requirements

### Requirement: Shared-bankroll portfolio selection ranks concurrent candidates
The portfolio risk/allocation layer SHALL support opt-in top-N selection that ranks concurrent candidates before shared bankroll is allocated.

#### Scenario: Concurrent candidates compete for capital
- **WHEN** multiple long-enabled candidates compete in the same allocation bucket
- **THEN** the selector orders them by algorithmic score, relative strength rank, relative friction, and deterministic symbol tie-breaker
- **AND** allocates capital only to the best-ranked candidates that fit portfolio caps.

#### Scenario: Candidate is not selected by rank
- **WHEN** a candidate is eligible but lower-ranked candidates cannot fit after higher-ranked allocation
- **THEN** the trade ledger retains the candidate with `accepted=false`
- **AND** blocker `portfolio_selection_rank_not_selected`
- **AND** the candidate does not consume exposure or affect PnL.

#### Scenario: Ranking is reported
- **WHEN** portfolio artifacts are written
- **THEN** they include selected/rejected counts and ranking values used for each candidate.
