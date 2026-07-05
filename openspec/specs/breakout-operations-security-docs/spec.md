# breakout-operations-security-docs Specification

## Purpose
Define local operational safety, degraded-mode protection, secret-handling, documentation, and deferred operator-surface requirements for the breakout strategy before any live or production execution scope is approved.
## Requirements
### Requirement: Monitoring and degraded mode protect trading
The system SHALL implement local health/degraded-mode checks that detect stale market data, configuration errors, fake broker/order mismatch, and risk-stop states, and SHALL block new entries while degraded.

#### Scenario: Degraded mode blocks entries
- **WHEN** any configured health check enters degraded state
- **THEN** entry generation or risk approval rejects new entries with an explicit degraded reason

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
The repository SHALL include task-oriented local documentation for setup, configuration, dry-run operation, operator workflows, API/web surfaces, test methodology, runbook procedures, deployment assumptions, security handling, QA checklist, config changelog expectations, and an up-to-date README overview of the current repository purpose, runtime entrypoints, research/backtest entrypoints, data/artifact locations, and safety limitations.

#### Scenario: Operator follows feed-gap runbook
- **WHEN** a feed-gap alert or degraded state occurs
- **THEN** the runbook explains how to inspect data health, trading mode, broker/fake adapter state, recovery conditions, and safe restart steps

#### Scenario: Reader or operator starts from README
- **WHEN** a reader opens `README.md`
- **THEN** it describes the repository as the current Bybit tradebot plus breakout screener/research codebase rather than a generic template
- **AND** it points to setup, verification, runtime, admin, breakout research/backtesting, artifact, OpenSpec, and operations documentation paths that exist in the repository
- **AND** it states credentialed behavior and dry-run/fake breakout execution limits without embedding secrets
- **AND** its main explanatory prose is written in Russian while preserving commands, paths, module names, and canonical technical terms as needed

### Requirement: Legal and broker constraints are configurable policy inputs
The system SHALL allow project-specific broker, exchange, and jurisdictional constraints to be documented and enforced as policy where applicable.

#### Scenario: Broker rate/order rule exists
- **WHEN** a broker has order frequency, order type, or position constraints
- **THEN** the execution/risk policy can block non-compliant intents before order submission

