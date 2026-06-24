## MODIFIED Requirements

### Requirement: Configuration is versioned and reproducible
The system SHALL persist validated breakout configuration versions with stable hashes and attach config hash/version identifiers to signals, risk decisions, fake/live execution records where applicable, and backtest or replay runs.

#### Scenario: Same config has same hash
- **WHEN** semantically identical configuration is serialized twice
- **THEN** the system produces the same config hash

### Requirement: Decision trace explains every trade decision
The system SHALL create first-class decision traces linking level discovery, feature values, score factors, scenario selection, entry mode, risk approval/rejection, execution/fake execution, position management, exits, and manual overrides.

#### Scenario: Risk rejection is replayable
- **WHEN** Risk Manager rejects an intent
- **THEN** the persisted trace includes the triggering signal or setup, risk inputs, rejection reason, config hash, and dataset/reference identifiers needed for replay
