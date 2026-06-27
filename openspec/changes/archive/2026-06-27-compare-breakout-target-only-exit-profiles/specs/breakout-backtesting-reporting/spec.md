# breakout-backtesting-reporting Specification Delta

## MODIFIED Requirements
### Requirement: Backtests compare fixed research exit profiles
The BTCUSDT batch research runner SHALL support disabled-by-default, fixed, named exit-profile comparisons for path-risk, stop, break-even, trailing, holding, target-only, and close-confirmed exit hypotheses while preserving the existing reference behavior when no exit profile is selected.

#### Scenario: Target-only exit profile is selected
- **WHEN** a supported target-only exit profile is selected
- **THEN** already-accepted long trades evaluate configured favorable intrabar or close-confirmed target thresholds from entry price using entry-time ATR and post-entry M15 bars only
- **AND** the profile remains disabled unless selected by its explicit name
- **AND** missing entry-time ATR records an explicit counter/reason and falls back to the configured maximum-hold close
- **AND** entry selection, lifecycle gates, M15 slope feature filtering, max-trades risk control, confirmation filters, and configured research thresholds remain unchanged.

### Requirement: Exit-profile batch summaries are auditable
BTCUSDT batch summaries SHALL expose exit-profile comparison results separately from gate, feature-filter, risk-control, regime-filter, and confirmation-filter dimensions.

#### Scenario: Target-only profile is evaluated against realistic costs
- **WHEN** a target-only profile is evaluated for the BTCUSDT quarterly `2023q1..2024q4` scorecard
- **THEN** success requires all eight quarters to pass after realistic costs with unchanged thresholds
- **AND** baseline-only pass counts are recorded as insufficient unless the realistic-cost scorecard also reaches `8/8`
- **AND** a candidate may stop after a failed required realistic-cost quarter only when the remaining required quarters are recorded as blocked/not run after early falsification and are not counted as passes
- **AND** a below-`8/8` result is archived as falsified research evidence with scorecard artifacts and no success notification.
