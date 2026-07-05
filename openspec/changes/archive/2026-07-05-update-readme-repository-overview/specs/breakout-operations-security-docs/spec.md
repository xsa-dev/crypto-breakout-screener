## MODIFIED Requirements

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
