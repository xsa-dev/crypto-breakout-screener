## ADDED Requirements

### Requirement: Portfolio selection artifacts expose cost-feasibility skips
The shared-bankroll portfolio batch report SHALL expose opt-in selection profile decisions as deterministic artifacts separate from regime decisions and exposure-cap decisions.

#### Scenario: Selection profile is disabled
- **WHEN** a portfolio batch is run without a selection profile
- **THEN** selection settings and skip counts indicate no active selection gate
- **AND** trade acceptance, exposure cap behavior, shared equity accounting, and existing report fields are preserved.

#### Scenario: Cost-feasibility gate skips an entry
- **WHEN** `cost-feasible-v1` evaluates a long-enabled trade candidate whose entry-time friction ratio exceeds the configured maximum
- **THEN** the portfolio trade CSV retains the candidate row with `accepted=false`
- **AND** the blocker is `portfolio_selection_cost_feasibility`
- **AND** the candidate does not consume shared open exposure or affect net PnL/equity
- **AND** selection skip counts include the blocker.

#### Scenario: Selection profile summary is exported
- **WHEN** the portfolio summary JSON and scorecard CSV are written
- **THEN** they include the selection profile name, selection settings, and per-window skip counts or artifact references
- **AND** per-regime contribution rows include selected-off signals in skipped/blocked signal counts.
