## ADDED Requirements

### Requirement: Portfolio cost-feasibility selection preserves the shared-bankroll success target
The crypto breakout research loop SHALL allow a deterministic, opt-in cost-feasibility selection profile for shared-bankroll altcoin portfolio hypotheses without weakening the fixed universe, realistic costs, configured thresholds, or required quarterly scorecard.

#### Scenario: Cost-feasibility profile is selected
- **WHEN** a shared-bankroll portfolio run selects `cost-feasible-v1`
- **THEN** the runner evaluates the approved fixed universe and required windows with one shared `10000 USDT` bankroll
- **AND** it keeps configured realistic spread, slippage, commission, funding, per-trade notional cap, total open-exposure cap, and research thresholds unchanged
- **AND** it skips long-enabled entries whose entry-time price/cost geometry is not feasible under the configured cost settings
- **AND** it records the skipped entries as blocked signals rather than deleting them from audit artifacts.

#### Scenario: Cost-feasibility profile is reported
- **WHEN** a portfolio scorecard is written for a run using a selection profile
- **THEN** the summary records `selection_profile`, `selection_settings`, and `selection_skip_counts`
- **AND** the per-regime report includes selection-skipped signals in skipped/blocked counts
- **AND** the trade ledger includes machine-readable selection blockers for skipped rows.

#### Scenario: Cost-feasibility profile reaches or fails portfolio success
- **WHEN** the cost-feasibility portfolio hypothesis is evaluated beyond smoke
- **THEN** success still requires all eight quarters `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, and `2024q4` to pass as one combined shared-bankroll portfolio under realistic costs with complete regime reporting and no missing feed gaps for the promoted universe run
- **AND** a result below `8/8` is recorded as falsified/negative evidence rather than success.
