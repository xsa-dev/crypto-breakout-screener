## MODIFIED Requirements

### Requirement: Monitoring and degraded mode protect trading
The system SHALL implement local health/degraded-mode checks that detect stale market data, configuration errors, fake broker/order mismatch, and risk-stop states, and SHALL block new entries while degraded.

#### Scenario: Degraded mode blocks entries
- **WHEN** any configured health check enters degraded state
- **THEN** entry generation or risk approval rejects new entries with an explicit degraded reason

### Requirement: Operator documentation is complete
The repository SHALL include task-oriented local documentation for setup, configuration, dry-run operation, operator workflows, API/web surfaces, test methodology, runbook procedures, deployment assumptions, security handling, QA checklist, and config changelog expectations.

#### Scenario: Operator follows feed-gap runbook
- **WHEN** a feed-gap alert or degraded state occurs
- **THEN** the runbook explains how to inspect data health, trading mode, broker/fake adapter state, recovery conditions, and safe restart steps
