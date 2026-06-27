## MODIFIED Requirements

### Requirement: Backtests compare fixed research exit profiles
The BTCUSDT batch research runner SHALL support disabled-by-default, fixed, named exit-profile comparisons for path-risk, stop, break-even, trailing, holding, target-only, close-confirmed, partial, protected residual, large-target, realized drawdown-guard, large-target close-stop, and occupancy-aware holding/target exit hypotheses while preserving the existing reference behavior when no exit, drawdown-guard, or occupancy profile is selected.

#### Scenario: Occupancy-aware holding profile is selected
- **WHEN** a supported occupancy-aware holding or target profile is selected
- **THEN** already-accepted long trades evaluate the configured fixed holding and optional favorable target thresholds using existing post-entry M15 bars only
- **AND** new entries are skipped while the previous simulated trade remains inside its holding interval
- **AND** the occupancy gate remains disabled unless selected by an explicit profile name
- **AND** skip counts include a machine-readable occupancy reason
- **AND** entry scoring, M15 slope feature filtering, max-trades risk control, confirmation filters, regime filters, cost assumptions, and configured research thresholds remain unchanged.

### Requirement: Exit-profile batch summaries are auditable
BTCUSDT batch summaries SHALL expose exit-profile, occupancy gate, and realized drawdown-guard comparison results separately from feature-filter, regime-filter, confirmation-filter, and cost dimensions.

#### Scenario: Occupancy-aware profile is evaluated against the quarterly scorecard
- **WHEN** an occupancy-aware holding or target profile is evaluated for the BTCUSDT quarterly `2023q1..2024q4` scorecard
- **THEN** success requires all eight quarters to pass unchanged configured research thresholds
- **AND** the summary records the occupancy setting, exit settings, cost settings, per-quarter metrics, blockers, and artifact paths
- **AND** no missing or skipped quarter is counted as a pass
- **AND** a below-`8/8` result is archived as falsified research evidence with no success notification.
