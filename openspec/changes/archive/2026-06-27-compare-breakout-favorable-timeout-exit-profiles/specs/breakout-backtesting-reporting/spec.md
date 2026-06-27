## MODIFIED Requirements

### Requirement: Backtests compare fixed research exit profiles
The BTCUSDT batch research runner SHALL support disabled-by-default, fixed, named exit-profile comparisons for path-risk, stop, break-even, trailing, holding, target-only, close-confirmed, delayed close-stop, partial, protected residual, large-target, realized drawdown-guard, large-target close-stop, occupancy-aware holding/target, exposure-scaled large-target, profit-lock trailing, and favorable-timeout exit hypotheses while preserving the existing reference behavior when no exit, drawdown-guard, occupancy, exposure-scaled, profit-lock trailing, or favorable-timeout profile is selected.

#### Scenario: Favorable-timeout profile is selected
- **WHEN** a supported favorable-timeout profile is selected by exact profile name
- **THEN** already-accepted long trades evaluate the configured favorable ATR threshold and timeout bar using existing post-entry M15 bars only
- **AND** a trade that has not reached the favorable threshold by the timeout bar exits at that bar close
- **AND** a trade that reaches the favorable threshold before or during the timeout bar continues to its configured target, close target, or fixed-hold fallback
- **AND** entry filters, research thresholds, cost model, data source, and default BTCUSDT behavior are unchanged
- **AND** the profile remains disabled unless selected explicitly.

### Requirement: Exit-profile batch summaries are auditable
BTCUSDT batch summaries SHALL expose exit-profile, delayed close-stop grace settings, occupancy gate, realized drawdown-guard, exposure-scaled, profit-lock trailing, and favorable-timeout comparison results separately from feature-filter, regime-filter, confirmation-filter, and cost dimensions.

#### Scenario: Favorable-timeout profile is evaluated against realistic costs
- **WHEN** a favorable-timeout profile is evaluated for the BTCUSDT quarterly `2023q1..2024q4` scorecard
- **THEN** success requires all eight quarters to pass after realistic costs with unchanged thresholds
- **AND** the summary records the target or close-target settings, favorable-timeout threshold and bar settings, cost settings, per-quarter metrics, blockers, and artifact paths
- **AND** no missing or skipped quarter is counted as a pass
- **AND** a below-`8/8` result is archived as falsified research evidence with no success notification.
