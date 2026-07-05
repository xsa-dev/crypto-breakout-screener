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

#### Scenario: Code agent indexes source documents
- **WHEN** a code agent or maintainer needs to use the repository documentation for breakout implementation, review, or research planning
- **THEN** the `docs/` tree provides a root documentation index and a code-agent usage guide
- **AND** source materials under `docs/ai/task/` are classified by role, including authoritative strategy sources, visual/PDF sources, research evidence, and indexing caveats
- **AND** a machine-readable source manifest lists every source material path, type, language, status, topics, and companion-text availability
- **AND** key source requirements have stable documentation IDs and source-to-spec/code traceability tables
- **AND** visual source materials that are not text-indexable have either a companion transcript/extracted text file or an explicit `needs_extraction` caveat
- **AND** the documentation warns that source strategy documents do not approve live/full-auto trading or override negative realistic-cost research evidence
- **AND** the indexing layer does not introduce source-code, dependency, lockfile, runtime, generated-artifact, live-trading, or credential changes
