## MODIFIED Requirements

### Requirement: Level engine detects supported level types
The level engine SHALL implement local deterministic detection for pivot high/low, round-number, daily high/low, cascade, and trendline/naklonnaya level candidates using only available historical input data.

#### Scenario: Level candidates include source metadata
- **WHEN** the level engine emits a level candidate
- **THEN** it includes level type, price, source bars or anchors, detection timestamp, and confidence inputs

### Requirement: Level validity uses touches, reaction, visibility, and recent-break rules
The level engine SHALL evaluate min touches, multi-timeframe visibility, reaction threshold, recent-break invalidation, and configurable tolerances before a level can be used by setup scoring.

#### Scenario: Recently broken level is invalidated
- **WHEN** price has recently broken through a candidate level within the configured lookback
- **THEN** the engine marks that candidate invalid with an explicit reason
