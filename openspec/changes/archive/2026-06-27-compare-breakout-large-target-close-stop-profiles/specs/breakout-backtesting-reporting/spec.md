# breakout-backtesting-reporting Specification Delta

## MODIFIED Requirements
### Requirement: Backtests compare fixed research exit profiles
The BTCUSDT batch research runner SHALL support disabled-by-default, fixed, named exit-profile comparisons for path-risk, stop, break-even, trailing, holding, target-only, close-confirmed, partial, protected residual, large-target, realized drawdown-guard, and large-target close-stop exit hypotheses while preserving the existing reference behavior when no exit or drawdown-guard profile is selected.

#### Scenario: Large-target close-stop profile is selected
- **WHEN** a supported large-target close-stop profile is selected
- **THEN** already-accepted long trades evaluate the configured close-confirmed adverse stop threshold and favorable intrabar or close-confirmed target threshold from entry price using entry-time ATR and post-entry M15 bars only
- **AND** the close-confirmed stop check is evaluated before favorable target checks on each post-entry bar
- **AND** the profile remains disabled unless selected by its explicit name
- **AND** missing entry-time ATR records an explicit counter/reason and falls back to the configured maximum-hold close
- **AND** entry scoring, M15 slope feature filtering, max-trades risk control, confirmation filters, regime filters, and configured research thresholds remain unchanged.

### Requirement: Exit-profile batch summaries are auditable
BTCUSDT batch summaries SHALL expose exit-profile and realized drawdown-guard comparison results separately from gate, feature-filter, risk-control, regime-filter, and confirmation-filter dimensions.

#### Scenario: Large-target close-stop profile is evaluated against realistic costs
- **WHEN** a large-target close-stop profile is evaluated for the BTCUSDT quarterly `2023q1..2024q4` scorecard
- **THEN** success requires all eight quarters to pass after realistic costs with unchanged thresholds
- **AND** the summary records the close-stop, target, holding, and cost settings
- **AND** baseline-only pass counts are recorded as insufficient unless the realistic-cost scorecard also reaches `8/8`
- **AND** a candidate may stop after a failed required realistic-cost quarter only when the remaining required quarters are recorded as blocked/not run after early falsification and are not counted as passes
- **AND** a below-`8/8` result is archived as falsified research evidence with scorecard artifacts and no success notification.
