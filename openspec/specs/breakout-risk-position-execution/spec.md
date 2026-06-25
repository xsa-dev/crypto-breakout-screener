# breakout-risk-position-execution Specification

## Purpose
Define broker-neutral trade intents, blocking risk approval, position sizing, add-on constraints, partial exits, and fake/idempotent execution semantics before any live adapter is approved.
## Requirements
### Requirement: Risk manager blocks execution
The system SHALL require Risk Manager approval before any order is sent. Signal Engine SHALL create `TradeIntent`; Execution Engine SHALL only act on approved intents. The Risk Manager SHALL approve or reject every trade and add-on intent before execution using score/context, stop distance, position sizing, add-on risk budget, daily loss, max-open-position, degraded-feed, and broker-state checks.

#### Scenario: Risk rejects trade
- **WHEN** Risk Manager rejects a `TradeIntent`
- **THEN** the system records the rejection reason
- **AND** no broker order is sent

#### Scenario: Daily loss blocks new entries
- **WHEN** realized or unrealized loss reaches the configured daily limit
- **THEN** every new entry intent is rejected with `daily_loss_limit`

### Requirement: Position size is derived from risk and stop distance
The system SHALL calculate position size using configured risk, equity, stop distance, and instrument multiplier. Baseline formula is `floor((equity * risk_pct) / stop_distance_money)` where `stop_distance_money = abs(entry_price - stop_price) * contract_multiplier`. Approved trade decisions SHALL report `planned_risk` using the same stop-distance money formula so approval audit data matches the risk-derived quantity.

#### Scenario: Position size is calculated
- **WHEN** equity, risk percent, entry, stop, and contract multiplier are known
- **THEN** Risk Manager calculates maximum allowed position size before execution
- **AND** the approved decision records multiplier-aware planned risk for the approved quantity

#### Scenario: Stop distance is invalid
- **WHEN** stop distance is zero, negative, or too small for instrument constraints
- **THEN** Risk Manager rejects the trade intent

### Requirement: Add-ons are risk-budgeted
The system SHALL allow add-ons only on new local-extremum breakouts, cascade-level breakouts, or valid retests. Add-ons SHALL be 10%-20% of position by default, no more than two, and SHALL NOT exceed remaining trade risk budget or degrade average price beyond configured limits.

#### Scenario: Add-on is approved
- **WHEN** a valid add-on trigger occurs and remaining risk budget is sufficient
- **THEN** Risk Manager may approve an add-on within configured share bounds

#### Scenario: Add-on worsens average too much
- **WHEN** proposed add-on would degrade average price beyond `degrade_avg_price_limit_atr`
- **THEN** Risk Manager rejects the add-on

#### Scenario: Price rolls back to add-on level
- **WHEN** price rolls back to the add-on level after an add-on
- **THEN** the system exits or reduces the added portion according to configured rules
- **AND** the decision trace records the add-on reset reason and remaining base position state

### Requirement: Density can define support and stop behavior
The system SHALL allow configured density/support to act as a trade-support premise and stop reference. When density is used as the support premise, local planning SHALL record the density reference, stop placement rule, and exit-on-density-eating rule. Density invalidation/eating against the trade SHALL produce a deterministic local reset/reduction decision with a machine-readable reason and remaining base position state.

#### Scenario: Density is used as support
- **WHEN** a setup uses density in the breakout direction as support
- **THEN** the trade plan records the density reference, stop placement rule, and exit-on-density-eating rule
- **AND** the stop reference is side-symmetric behind the density

#### Scenario: Density is eaten against the trade
- **WHEN** the density used as support is eaten or invalidated against the trade
- **THEN** the system exits or reduces the affected position according to configured risk policy
- **AND** the decision trace records `density_eaten` and remaining base position state

### Requirement: Partial exits follow 30/50/20 framework
The system SHALL support first fixation of 30%, second fixation of 50%, and final 20% runner/trailer as baseline exit framework.

#### Scenario: First fixation executes
- **WHEN** the first target/impulse condition is reached
- **THEN** the system exits 30% of total planned volume
- **AND** moves stop to breakeven or protected plus when configured

#### Scenario: First fixation uses three cascade limits
- **WHEN** first fixation is planned with PDF-style cascade execution
- **THEN** the 30% first fixation may be split into three limit orders placed near spread/first impulse targets according to configuration

#### Scenario: Second fixation executes
- **WHEN** second target or acceleration condition is reached
- **THEN** the system exits 50% of total planned volume according to cascade/limit distribution rules

#### Scenario: Second fixation uses acceleration or five limits
- **WHEN** second fixation is planned with PDF-style cascade execution
- **THEN** the 50% second fixation may be exited on accelerations or split into five pre-placed limit orders before opposing densities within configured potential/RR bounds

#### Scenario: Runner remains
- **WHEN** first and second fixations are complete and trend structure remains valid
- **THEN** the remaining 20% may trail by structure, ATR, or last cascade level

#### Scenario: Runner is held only in favorable movement
- **WHEN** the final 20% runner remains after partial exits
- **THEN** it stays open only while configured trend/structure continuation conditions remain valid

### Requirement: Fast exit mode handles low breakouts
The system SHALL provide a `fast_exit_for_low_breakouts` option because low breakouts can accelerate on long liquidations/stops. When enabled for an explicitly identified short low-breakout scenario with positive planned quantity, local exit planning SHALL use an accelerated no-runner framework and record a machine-readable fast-exit reason. When disabled, when quantity is not positive, or when the setup is not a short low-breakout scenario, the baseline 30/50/20 framework SHALL remain unchanged.

#### Scenario: Fast exit is enabled
- **WHEN** a low-breakout short scenario reaches configured fast-exit conditions
- **THEN** the system exits faster than the default high-breakout runner framework
- **AND** the exit plan records `fast_exit_low_breakout`

#### Scenario: Fast exit falls back for non-low-breakout conditions
- **WHEN** `fast_exit_for_low_breakouts` is disabled or the setup is not an explicitly identified short low-breakout scenario
- **THEN** the system uses the baseline 30/50/20 exit framework
- **AND** the exit plan records a non-fast-exit reason

### Requirement: Execution adapter is idempotent and synchronized
The system SHALL send, cancel, modify, and query orders through an execution adapter that records broker references and reconciles positions/orders after reconnect or restart. This change SHALL implement execution interfaces and fake adapters sufficient for deterministic tests, while concrete live broker/exchange/terminal adapters remain blocked until a later dedicated OpenSpec change approves them.

#### Scenario: Reconnect after order submission
- **WHEN** the system reconnects after a submitted order
- **THEN** it queries broker state and avoids duplicate orders for the same approved intent

#### Scenario: Broker state mismatch
- **WHEN** local state differs from broker order/position state
- **THEN** the system records an order-mismatch/risk event and blocks new entries until resolved by policy

#### Scenario: Fake adapter records idempotent order behavior
- **WHEN** the same order request id is submitted twice to the fake adapter
- **THEN** the adapter returns the existing simulated order result without creating a duplicate order

