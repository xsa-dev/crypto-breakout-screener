# breakout-setup-scoring Specification

## Purpose
Specify deterministic breakout setup feature calculation, score eligibility thresholds, scenario priority, and context-filter behavior.
## Requirements
### Requirement: Setup evaluator calculates required factors
The setup scorer SHALL calculate ATR, EMA50/EMA200, ADX where available, consolidation/protorgovka, slow approach, activity, and density/proxy feature values from canonical data before selecting a breakout scenario.

#### Scenario: Consolidation factor is scored
- **WHEN** price range compresses, ATR falls, or variance decreases over `consolidation_bars`
- **THEN** the system assigns a consolidation score from 0 to the configured weight

#### Scenario: Slow approach factor is scored
- **WHEN** price approaches the level with velocity not exceeding `slow_approach_max_velocity` and without sharp counterstructure breaks
- **THEN** the system assigns a slow-approach score from 0 to the configured weight

#### Scenario: Trend factor is scored
- **WHEN** trend filter is enabled
- **THEN** the system scores long context using EMA50 > EMA200 and ADX above threshold, with symmetric short rules

#### Scenario: Activity factor is scored
- **WHEN** volume, tick activity, or configured proxy rises during compression or breakout
- **THEN** the system assigns an activity score from 0 to the configured weight

#### Scenario: Missing optional density data is handled
- **WHEN** no order-book/density source is configured
- **THEN** setup scoring records density as unavailable or uses an approved proxy
- **AND** the missing optional feature does not crash core setup evaluation

#### Scenario: Density factor is scored
- **WHEN** order book density or an approved proxy supports the breakout direction
- **THEN** the system assigns a density/support score from 0 to the configured weight

### Requirement: Breakout score controls trade eligibility
The setup scorer SHALL implement configured factor weights, 70/50 thresholds, and explicit low-score rejection reasons. The system SHALL compute `breakout_score` as the sum of configured factor scores. Baseline thresholds SHALL be `score >= 70` for normal risk, `50 <= score < 70` for reduced risk, and `score < 50` for no trade.

#### Scenario: Score class is explicit
- **WHEN** a setup is scored
- **THEN** the result exposes numeric factor scores, configured weights, total score, threshold class, selected scenario if any, and rejection reasons if blocked

#### Scenario: Normal-risk score
- **WHEN** `breakout_score` is 70 or higher
- **THEN** the setup is eligible for normal-risk review by Risk Manager

#### Scenario: Reduced-risk score
- **WHEN** `breakout_score` is at least 50 and below 70
- **THEN** the setup is eligible only for reduced-risk review

#### Scenario: Low score
- **WHEN** `breakout_score` is below 50
- **THEN** the system rejects the setup before order intent generation

### Requirement: Scenario selection is deterministic
The setup scorer SHALL implement and choose at most one primary scenario per level/setup using the configured priority order: consolidation breakout, cascade-level breakout, local-extremum breakout near the level, trendline/naklonnaya breakout, density-supported breakout.

#### Scenario: Priority order is explicit
- **WHEN** multiple setup scenarios match
- **THEN** the scorer chooses the configured highest-priority primary scenario

#### Scenario: Multiple scenarios match
- **WHEN** consolidation and density-supported breakout conditions are both true
- **THEN** the system selects consolidation breakout as the primary scenario
- **AND** records density support as a supporting factor

### Requirement: Context filters can block technically valid breakouts
The system SHALL apply configured market-direction and “поводырь” context filters such as EMA direction, ADX, DXY, US10Y, silver/gold, SP500/Nasdaq, or approved market-specific proxies. Local setup scoring SHALL accept deterministic context-driver signals supplied by upstream data providers, SHALL NOT fetch external context instruments itself, and SHALL record explicit score-penalty or blocking reasons when context drivers oppose the breakout direction.

#### Scenario: Context sharply opposes breakout
- **WHEN** a configured context driver strongly moves against the breakout direction
- **THEN** the system lowers score or rejects the setup according to configuration

#### Scenario: Context driver hard-blocks a setup
- **WHEN** an enabled context driver opposes the breakout side at or above the configured hard-block threshold
- **THEN** setup scoring returns blocked eligibility
- **AND** rejection reasons include `context_filter_blocked` and the driver reason

#### Scenario: Context driver lowers but does not block score
- **WHEN** an enabled context driver opposes the breakout side below the configured hard-block threshold
- **THEN** setup scoring reduces the numeric breakout score by the configured deterministic penalty
- **AND** recalculates normal/reduced/blocked eligibility from the adjusted score

#### Scenario: Context filter is side-aware
- **WHEN** a context driver opposes the opposite breakout side rather than the evaluated side
- **THEN** setup scoring does not penalize or block the evaluated setup because of that driver

### Requirement: Setup scoring can use Heikin-Ashi as a derived feature view
The breakout setup scoring system SHALL support opt-in Heikin-Ashi-derived features while preserving raw OHLCV for economic accounting.

#### Scenario: Named Heikin-Ashi profiles are available
- **WHEN** a historical runner or programmatic caller requests Heikin-Ashi-based behavior
- **THEN** the implementation exposes named profiles `heikin-ashi-trend-filter-v1`, `heikin-ashi-confirmation-v1`, and `heikin-ashi-exit-v1`
- **AND** reports active Heikin-Ashi profile names separately from raw feature, confirmation, and exit profile names.

#### Scenario: Heikin-Ashi features are enabled
- **WHEN** a setup score profile enables Heikin-Ashi features
- **THEN** feature snapshots include Heikin-Ashi body ratio, wick ratios, close location, color, color streak, trend persistence, compression, reversal hint, and failed-continuation hint where computable
- **AND** the score artifact labels them as derived features.

#### Scenario: Heikin-Ashi features are disabled
- **WHEN** a profile does not enable Heikin-Ashi
- **THEN** default raw-candle feature behavior is preserved.

#### Scenario: Heikin-Ashi does not replace density
- **WHEN** Heikin-Ashi features are used with no DOM/L2 data
- **THEN** density/support source remains `ohlcv_proxy` or `unavailable`
- **AND** the report does not claim real order book density was tested.
