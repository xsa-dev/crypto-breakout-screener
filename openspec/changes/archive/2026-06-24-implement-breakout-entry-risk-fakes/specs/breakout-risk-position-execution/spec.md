## MODIFIED Requirements

### Requirement: Risk manager blocks execution
The system SHALL require Risk Manager approval before any order is sent. Signal Engine SHALL create `TradeIntent`; Execution Engine SHALL only act on approved intents. The Risk Manager SHALL approve or reject every trade and add-on intent before execution using score/context, stop distance, position sizing, add-on risk budget, daily loss, max-open-position, degraded-feed, and broker-state checks.

#### Scenario: Risk rejects trade
- **WHEN** Risk Manager rejects a `TradeIntent`
- **THEN** the system records the rejection reason
- **AND** no broker order is sent

#### Scenario: Daily loss blocks new entries
- **WHEN** realized or unrealized loss reaches the configured daily limit
- **THEN** every new entry intent is rejected with `daily_loss_limit`

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
