## ADDED Requirements

### Requirement: Monitoring and degraded mode protect trading
The system SHALL provide healthchecks and alerts for market data feed gaps, broker disconnects, order mismatches, risk stops, configuration errors, and abnormal trading behavior.

#### Scenario: Market data feed is lost
- **WHEN** live market data becomes stale beyond configured tolerance
- **THEN** the system enters degraded mode
- **AND** no new trades are opened until data health recovers

#### Scenario: Daily loss limit is reached
- **WHEN** realized/unrealized loss reaches `max_daily_loss_pct` policy threshold
- **THEN** Risk Manager blocks all new entries until the configured reset condition

### Requirement: Restart and reconnect are safe
The system SHALL synchronize broker orders and positions after restart or reconnect before permitting new entries.

#### Scenario: Service restarts with open position
- **WHEN** the service starts and broker reports open positions or active orders
- **THEN** the system reconciles state and prevents duplicate orders

### Requirement: Operator UI/API MVP is defined and deferred from foundation slice
The system SHALL define an operator surface MVP including config editor, signal list, levels list, decision trace view, backtest run list, manual confirm/reject for semi-auto, and health/status page. This UI/API implementation SHALL be deferred beyond the foundation slice unless a later OpenSpec change approves it.

#### Scenario: MVP operator surface is reviewed
- **WHEN** UI/API scope is selected for a later implementation slice
- **THEN** it includes config editing, signals, levels, decision traces, backtest runs, semi-auto confirmation/rejection, and health/status views

#### Scenario: Foundation slice is implemented
- **WHEN** only the foundation slice is approved
- **THEN** UI/API implementation remains out of scope except for code interfaces needed by tests

### Requirement: Secrets and credentials are never stored in source
The system SHALL keep API keys, terminal logins, access tokens, and passwords out of source code, committed docs, and normal logs.

#### Scenario: Secret is configured
- **WHEN** a broker or notification credential is required
- **THEN** it is loaded from an approved secret source and redacted in logs/errors

### Requirement: Security baseline is documented
The system SHALL document least-privilege API access, secret rotation, role separation for developer/operator/admin, TLS for external connections, immutable audit-log expectations, and business/security event logging.

#### Scenario: Deployment guide is produced
- **WHEN** deployment documentation is delivered
- **THEN** it includes secret handling, environment variables, permissions, network/TLS assumptions, backup/rollback, and incident contacts/checklists

### Requirement: Operator documentation is complete
The system SHALL include user guide, operator guide, API specification, configuration manual, test methodology, test report, deployment guide, runbook, changelog/config changelog, and QA checklists.

#### Scenario: Operator handles feed gap
- **WHEN** a feed-gap alert occurs
- **THEN** the runbook explains how to inspect data health, trading mode, broker state, and recovery conditions

#### Scenario: QA checklist is run
- **WHEN** QA validates a release
- **THEN** it checks feed loss, restart sync, duplicate data, invalid config, daily loss stop, false breakout handling, first fixation stop movement, and add-on risk rejection

### Requirement: Legal and broker constraints are configurable policy inputs
The system SHALL allow project-specific broker, exchange, and jurisdictional constraints to be documented and enforced as policy where applicable.

#### Scenario: Broker rate/order rule exists
- **WHEN** a broker has order frequency, order type, or position constraints
- **THEN** the execution/risk policy can block non-compliant intents before order submission
