## MODIFIED Requirements

### Requirement: Risk Manager blocks unsafe intents before execution
The Risk Manager SHALL approve or reject every trade and add-on intent before execution using score/context, stop distance, position sizing, add-on risk budget, daily loss, max-open-position, degraded-feed, and broker-state checks.

#### Scenario: Daily loss blocks new entries
- **WHEN** realized or unrealized loss reaches the configured daily limit
- **THEN** every new entry intent is rejected with `daily_loss_limit`

### Requirement: Execution adapters remain fake-only in this slice
This change SHALL implement execution interfaces and fake adapters sufficient for deterministic tests, while concrete live broker/exchange/terminal adapters remain blocked until a later dedicated OpenSpec change approves them.

#### Scenario: Fake adapter records idempotent order behavior
- **WHEN** the same order request id is submitted twice to the fake adapter
- **THEN** the adapter returns the existing simulated order result without creating a duplicate order
