# breakout-level-engine Specification

## Purpose
Specify deterministic breakout level detection, validation, and auditability for pivot, round-number, daily, cascade, and trendline levels.

## Requirements
### Requirement: Level engine detects supported level types
The level engine SHALL implement local deterministic detection and classification for pivot high, pivot low, round number, daily high/low, cascade, and trendline/naklonnaya level candidates using only available historical input data.

#### Scenario: Level candidates include source metadata
- **WHEN** the level engine emits a level candidate
- **THEN** it includes level type, price, source bars or anchors, detection timestamp, and confidence inputs

#### Scenario: Pivot high is confirmed
- **WHEN** a bar high is greater than the configured left-window highs and right-window highs after the right window closes
- **THEN** the system records a pivot-high level candidate

#### Scenario: Pivot low is confirmed
- **WHEN** a bar low is lower than the configured left-window lows and right-window lows after the right window closes
- **THEN** the system records a pivot-low level candidate

#### Scenario: Round number is near price action
- **WHEN** price action approaches a configured `round_step` multiple within `touch_tolerance_atr`
- **THEN** the system records or updates a round-number level candidate

#### Scenario: Daily high or low is available
- **WHEN** previous or current-session D1 high/low is available according to configuration
- **THEN** the system records daily high/low levels with elevated intraday priority metadata

#### Scenario: Cascade levels are found
- **WHEN** local levels form a sequence in the movement direction with count at least `cascade_min_count` and gaps no wider than `cascade_gap_atr`
- **THEN** the system records a cascade-level structure

#### Scenario: Trendline has enough touches
- **WHEN** at least three local touches form a trendline within configured angle and tolerance limits
- **THEN** the system records a trendline/naklonnaya level

### Requirement: Level validity uses touches, reaction, visibility, and recent-break rules
The level engine SHALL evaluate min touches, multi-timeframe visibility, reaction threshold, recent-break invalidation, and configurable tolerances before a level can be used by setup scoring.

#### Scenario: Too few touches
- **WHEN** a level has fewer than `min_touches`
- **THEN** the level is not eligible for breakout scenarios

#### Scenario: Reaction is insufficient
- **WHEN** the reaction from a level is below `min_reaction_atr * ATR(H1)` or configured equivalent
- **THEN** the level is not considered significant

#### Scenario: Recently broken level is invalidated
- **WHEN** price has recently broken through a candidate level within the configured lookback
- **THEN** the engine marks that candidate invalid with an explicit reason

### Requirement: Level output is auditable
The system SHALL store level type, symbol, price, timeframe, touches, source bars, created time, invalidation time, and reason codes.

#### Scenario: Level is invalidated
- **WHEN** price action invalidates a level by configured breakout or structure rules
- **THEN** the level record includes `invalidated_at` and an invalidation reason
