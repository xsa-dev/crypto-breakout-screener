## MODIFIED Requirements

### Requirement: Breakout research implements the supplied screener documentation
The breakout research loop SHALL treat `docs/ai/task` as the primary algorithmic source for the screener/trading-system strategy and SHALL NOT replace it with unrelated strategy invention.

#### Scenario: No active change exists but local evidence contains a next hypothesis
- **WHEN** no active OpenSpec change exists
- **AND** current specs, archived recommendations, docs, tests, code comments, or diagnostic artifacts identify a bounded unresolved breakout hypothesis
- **THEN** the research loop treats that hypothesis as a local task
- **AND** creates exactly one narrow OpenSpec change for that hypothesis before implementation

### Requirement: Source research documents are readable and render cleanly
Source research documents under `docs/ai/task/` that guide breakout implementation SHALL be readable in normal Markdown viewers and SHALL avoid broken generated citation artifacts, unbalanced code fences, and avoidable preview-breaking diagram syntax.

#### Scenario: Deep research report is opened by a reader
- **WHEN** a reader opens `docs/ai/task/deep-research-report.md`
- **THEN** the H1 title matches the repository name
- **AND** the main prose is Russian-first and scan-friendly
- **AND** raw generated citation artifacts such as `...` are not visible
- **AND** fenced code blocks are balanced
- **AND** Mermaid diagrams use GitHub-safe syntax and do not rely on fragile reverse flowchart arrows
- **AND** the document preserves the substantive strategy, risk, FSM, architecture, configuration, testing, acceptance, documentation, and security requirements
- **AND** the cleanup does not introduce source-code, dependency, runtime, live-trading, generated-artifact, or credential changes
