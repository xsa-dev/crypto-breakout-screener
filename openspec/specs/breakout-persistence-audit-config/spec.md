# breakout-persistence-audit-config Specification

## Purpose
Define the reproducible configuration, persistence, replay identifiers, and audit-trace contracts for breakout strategy decisions across research, fake execution, and operator review.

## Requirements
### Requirement: Configuration is versioned and reproducible
The system SHALL persist validated breakout configuration versions with stable hashes and attach config hash/version identifiers to signals, risk decisions, fake/live execution records where applicable, and backtest or replay runs.

#### Scenario: Same config has same hash
- **WHEN** semantically identical configuration is serialized twice
- **THEN** the system produces the same config hash

### Requirement: Stable machine-readable enums are defined
The system SHALL use stable machine-readable values for modes, level types, scenario types, entry modes, finite-state-machine states, and risk rejection reasons.

#### Scenario: Operation modes are serialized
- **WHEN** operation mode is persisted or exchanged through APIs
- **THEN** it uses one of `advisory_only`, `semi_auto`, or `full_auto`

#### Scenario: Level type is serialized
- **WHEN** a level is persisted
- **THEN** its type uses one of `pivot_high`, `pivot_low`, `round_number`, `daily_high`, `daily_low`, `cascade`, or `trendline`

#### Scenario: Scenario type is serialized
- **WHEN** a breakout scenario is persisted
- **THEN** its type uses one of `consolidation_breakout`, `cascade_breakout`, `local_extremum_breakout`, `trendline_breakout`, or `density_supported_breakout`

#### Scenario: Entry mode is serialized
- **WHEN** an entry intent is persisted
- **THEN** its entry mode uses one of `pre_entry`, `at_level`, or `post_breakout`

#### Scenario: FSM state is serialized
- **WHEN** a state-machine transition is persisted
- **THEN** its state uses one of `LEVEL_SEARCH`, `SETUP_READY`, `SCENARIO_PICK`, `ENTRY_MODE_PICK`, `POSITION_OPEN`, `BREAKOUT_CONFIRM`, `RETEST_MONITOR`, `ADDON_MONITOR`, `PARTIAL_EXIT`, `FALSE_BREAKOUT`, or `COMPLETE`

#### Scenario: Risk rejection reason is serialized
- **WHEN** Risk Manager rejects a trade or add-on
- **THEN** it uses a stable reason such as `score_too_low`, `context_filter_blocked`, `daily_loss_limit`, `max_positions`, `invalid_stop_distance`, `insufficient_risk_budget`, `addon_degrades_average`, `feed_degraded`, or `broker_state_mismatch`

### Requirement: Baseline parameters are represented
The system SHALL represent baseline parameters from the source materials, including pivot windows, min touches, recent break lookback, ATR/touch tolerances, `protorgovka_range_percent`, consolidation, slow approach, EMA/ADX, score weights/thresholds, entry shares, retest, false breakout, add-ons, exits, risk limits, timeframes, and execution mode.

#### Scenario: Baseline config is loaded
- **WHEN** the baseline breakout configuration is loaded
- **THEN** it includes score weights 20/20/20/20/20, entry shares 0.30/0.30/0.40, exit shares 0.30/0.50/0.20, default `protorgovka_range_percent` 0.3%-2.0%, and default execution mode `semi_auto`

### Requirement: Persistence entities cover market, strategy, execution, risk, and research data
The system SHALL persist or be able to derive audited records for bars, ticks, optional order book, levels, features, signals, orders, fills, positions, risk events, backtest runs, config versions, and decision traces.

#### Scenario: Signal is recorded
- **WHEN** Signal Engine produces a breakout signal
- **THEN** the signal record includes symbol, timestamp, side, scenario, score, factor details, and level reference

#### Scenario: Fill is recorded
- **WHEN** broker reports an execution fill
- **THEN** the fill record includes order reference, timestamp, fill price, fill quantity, fee when available, and source metadata

#### Scenario: Backtest run is recorded
- **WHEN** a backtest completes
- **THEN** the backtest run record includes config hash, dataset hash, time range, and metrics payload

### Requirement: Storage ownership is explicit
The system SHALL keep score factors owned by the signal/feature decision record, risk rejection reasons owned by risk events and linked trade intents, decision traces as first-class records linked to the triggering signal or backtest decision, and execution records linked in the chain `signals → orders → fills → positions` when execution exists.

#### Scenario: Score factors are stored
- **WHEN** a breakout score is calculated
- **THEN** the factor scores and weights are stored with the signal or feature-decision record and referenced by the decision trace

#### Scenario: Risk rejection is stored
- **WHEN** Risk Manager rejects a trade intent
- **THEN** the rejection reason is stored in a risk event and linked to the signal/trade intent decision trace

#### Scenario: Execution chain is stored
- **WHEN** an approved trade creates orders and fills
- **THEN** orders reference the signal or trade intent, fills reference orders, and positions reference fills or aggregated execution state

### Requirement: Replay-required fields are explicit
The system SHALL store or reference enough fields to reproduce decisions: canonical market data identifiers, symbol, timeframe, timestamps, level id/type/price/source bars, feature vector, score factors, config hash, dataset hash for research runs, operation mode, side, scenario, entry mode, FSM transition history, risk inputs, and manual override events.

#### Scenario: Decision is replayed
- **WHEN** a stored decision trace is replayed with the referenced dataset and config hash
- **THEN** the system can recompute the same level eligibility, score, scenario, and risk decision or report an explicit unavailable dependency

### Requirement: Decision trace explains every trade decision
The system SHALL create first-class decision traces linking level discovery, feature values, score factors, scenario selection, entry mode, risk approval/rejection, execution/fake execution, position management, exits, and manual overrides.

#### Scenario: Risk rejection is replayable
- **WHEN** Risk Manager rejects an intent
- **THEN** the persisted trace includes the triggering signal or setup, risk inputs, rejection reason, config hash, and dataset/reference identifiers needed for replay

### Requirement: Manual overrides are audited
The system SHALL record operator confirmations, rejections, manual overrides, and parameter changes with actor, time, reason, and affected entity.

#### Scenario: Operator confirms semi-auto trade
- **WHEN** an operator confirms a semi-auto trade intent
- **THEN** the system records actor, timestamp, intent reference, and confirmation result

