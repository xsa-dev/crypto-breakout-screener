## MODIFIED Requirements

### Requirement: Setup evaluator calculates required factors
The setup scorer SHALL calculate ATR, EMA50/EMA200, ADX where available, consolidation/protorgovka, slow approach, activity, and density/proxy feature values from canonical data.

#### Scenario: Missing optional density data is handled
- **WHEN** no order-book/density source is configured
- **THEN** setup scoring records density as unavailable or uses an approved proxy
- **AND** the missing optional feature does not crash core setup evaluation

### Requirement: Breakout score controls trade eligibility
The setup scorer SHALL implement configured factor weights, 70/50 thresholds, and explicit low-score rejection reasons.

#### Scenario: Score class is explicit
- **WHEN** a setup is scored
- **THEN** the result exposes numeric factor scores, configured weights, total score, threshold class, selected scenario if any, and rejection reasons if blocked

### Requirement: Scenario selection is deterministic
The setup scorer SHALL implement scenario priority order for consolidation, cascade, local extremum, trendline, and density-supported breakouts.

#### Scenario: Priority order is explicit
- **WHEN** multiple setup scenarios match
- **THEN** the scorer chooses the configured highest-priority primary scenario
