# breakout-backtesting-reporting Specification Delta

## MODIFIED Requirements

### Requirement: Backtests compare fixed research exit profiles
The BTCUSDT batch research runner SHALL support disabled-by-default, fixed, named exit-profile comparisons for path-risk, stop, break-even, trailing, and holding hypotheses while preserving the existing reference behavior when no exit profile is selected.

#### Scenario: Exit profile is disabled
- **WHEN** a backtest or batch runs without a configured exit profile
- **THEN** trade selection, one-bar close exits, realized metrics, run inputs, and verdict logic remain equivalent to the existing reference behavior
- **AND** exit profile settings and counters are empty or disabled.

#### Scenario: Fixed holding profile is selected
- **WHEN** a supported fixed holding exit profile is selected
- **THEN** already-accepted trades exit at the configured future M15 bar close or the last available post-entry bar when the configured horizon is unavailable
- **AND** the profile does not affect level detection, setup scoring, gates, feature filters, confirmation filters, risk sizing, or entry selection.

#### Scenario: Extended holding profile is selected
- **WHEN** a supported extended holding exit profile for `8`, `16`, or `32` M15 bars is selected
- **THEN** the runner applies only the named fixed holding horizon while preserving reference entry selection, lifecycle gates, M15 slope feature filter, max-trades risk control, confirmation filters, and configured research thresholds
- **AND** the profile remains disabled unless selected by its explicit name.

#### Scenario: Fixed ATR stop/target profile is selected
- **WHEN** a supported ATR stop/target exit profile is selected
- **THEN** already-accepted long trades evaluate fixed adverse stop and favorable target thresholds from entry price using entry-time ATR
- **AND** if stop and target are touched in the same bar, the stop is selected first
- **AND** missing entry-time ATR records an explicit counter/reason and falls back to the configured maximum-hold close.

#### Scenario: Break-even exit profile is selected
- **WHEN** a supported break-even exit profile is selected
- **THEN** already-accepted long trades activate break-even protection only after price first reaches the configured favorable ATR threshold from entry
- **AND** a later touch of the entry price exits at entry without using future bars
- **AND** missing entry-time ATR records an explicit counter/reason and falls back to the configured maximum-hold close.

#### Scenario: Trailing exit profile is selected
- **WHEN** a supported trailing exit profile is selected
- **THEN** already-accepted long trades activate trailing protection only after price first reaches the configured favorable ATR threshold from entry
- **AND** the trailing stop is calculated from the maximum high observed after activation minus the configured ATR giveback
- **AND** missing entry-time ATR records an explicit counter/reason and falls back to the configured maximum-hold close.

### Requirement: Exit-profile batch summaries are auditable
BTCUSDT batch summaries SHALL expose exit-profile comparison results separately from gate, feature-filter, risk-control, regime-filter, and confirmation-filter dimensions.

#### Scenario: Batch summary is written
- **WHEN** a batch runs with an exit profile
- **THEN** every summary window records `exit_profile`, `exit_profile_settings_json`, and `exit_profile_counts_json`
- **AND** summary JSON includes the selected exit profile and settings
- **AND** configured research thresholds and verdict logic are not weakened.

#### Scenario: Quarterly comparison completes
- **WHEN** quarterly 2023-2024 BTCUSDT batches finish for fixed exit profiles
- **THEN** the report states pass/fail status for `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, and `2024q4`
- **AND** remaining failed windows list blockers
- **AND** the report states whether any exit profile reached `8/8` after realistic costs, moved the score toward `8/8`, or failed to support the hypothesis.

#### Scenario: Extended holding profile is evaluated against realistic costs
- **WHEN** an extended holding profile is evaluated for the BTCUSDT quarterly 2023q1..2024q4 scorecard
- **THEN** success requires all eight quarters to pass after realistic costs with unchanged thresholds
- **AND** baseline-only pass counts are recorded as insufficient unless the realistic-cost scorecard also reaches `8/8`
- **AND** a below-`8/8` result is archived as falsified research evidence with scorecard artifacts and no success notification
