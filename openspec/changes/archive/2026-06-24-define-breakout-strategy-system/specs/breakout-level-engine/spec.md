## ADDED Requirements

### Requirement: Level engine detects supported level types
The system SHALL detect and classify pivot high, pivot low, round number, daily high/low, cascade, and trendline/naklonnaya levels.

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
The system SHALL validate levels using minimum touches, significant reaction, visibility on configured timeframes, and no recent invalidating breakout.

#### Scenario: Too few touches
- **WHEN** a level has fewer than `min_touches`
- **THEN** the level is not eligible for breakout scenarios

#### Scenario: Reaction is insufficient
- **WHEN** the reaction from a level is below `min_reaction_atr * ATR(H1)` or configured equivalent
- **THEN** the level is not considered significant

#### Scenario: Recent break invalidates level
- **WHEN** a level was broken within `recent_break_lookback_bars`
- **THEN** the level is rejected until it becomes valid again by configured rules

### Requirement: Level output is auditable
The system SHALL store level type, symbol, price, timeframe, touches, source bars, created time, invalidation time, and reason codes.

#### Scenario: Level is invalidated
- **WHEN** price action invalidates a level by configured breakout or structure rules
- **THEN** the level record includes `invalidated_at` and an invalidation reason
