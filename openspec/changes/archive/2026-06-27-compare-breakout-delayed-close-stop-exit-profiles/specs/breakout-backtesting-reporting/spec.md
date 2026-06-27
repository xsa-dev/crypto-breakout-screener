## MODIFIED Requirements

### Requirement: Backtests compare fixed research exit profiles
The BTCUSDT batch research runner SHALL support disabled-by-default, fixed, named exit-profile comparisons for path-risk, stop, break-even, trailing, holding, target-only, close-confirmed, delayed close-stop, partial, protected residual, large-target, realized drawdown-guard, large-target close-stop, occupancy-aware holding/target, and exposure-scaled large-target exit hypotheses while preserving the existing reference behavior when no exit, drawdown-guard, occupancy, or exposure-scaled profile is selected.

#### Scenario: Exposure-scaled large-target profile is selected
- **WHEN** a supported exposure-scaled large-target profile is selected
- **THEN** already-accepted long trades evaluate the configured large-target or close-target holding exit using existing post-entry M15 bars only
- **AND** the candidate uses its explicit fixed `base_quantity` setting while preserving the existing initial equity and research thresholds
- **AND** the exposure-scaled profile remains disabled unless selected by an explicit profile name
- **AND** entry scoring, M15 slope feature filtering, max-trades risk control, confirmation filters, regime filters, cost assumptions, and configured research thresholds remain unchanged.

#### Scenario: Delayed close-stop profile is selected
- **WHEN** a supported delayed close-stop profile is selected
- **THEN** already-accepted long trades evaluate the configured close-stop threshold only after the explicit grace-bar count has elapsed
- **AND** target or close-target behavior, fixed holding fallback, entry scoring, M15 slope feature filtering, max-trades risk control, confirmation filters, regime filters, cost assumptions, and configured research thresholds remain unchanged
- **AND** the delayed close-stop profile remains disabled unless selected by an explicit profile name.

### Requirement: Exit-profile batch summaries are auditable
BTCUSDT batch summaries SHALL expose exit-profile, delayed close-stop grace settings, occupancy gate, realized drawdown-guard, and exposure-scaled comparison results separately from feature-filter, regime-filter, confirmation-filter, and cost dimensions.

#### Scenario: Delayed close-stop profile is evaluated against realistic costs
- **WHEN** a delayed close-stop profile is evaluated for the BTCUSDT quarterly `2023q1..2024q4` scorecard
- **THEN** success requires all eight quarters to pass after realistic costs with unchanged thresholds
- **AND** the summary records the delayed close-stop settings, cost settings, per-quarter metrics, blockers, and artifact paths
- **AND** no missing or skipped quarter is counted as a pass
- **AND** a below-`8/8` result is archived as falsified research evidence with no success notification.

#### Scenario: Exposure-scaled profile is evaluated against realistic costs
- **WHEN** an exposure-scaled large-target profile is evaluated for the BTCUSDT quarterly `2023q1..2024q4` scorecard
- **THEN** success requires all eight quarters to pass after realistic costs with unchanged thresholds
- **AND** the summary records the exposure setting, exit settings, cost settings, per-quarter metrics, blockers, and artifact paths
- **AND** no missing or skipped quarter is counted as a pass
- **AND** a below-`8/8` result is archived as falsified research evidence with no success notification.
