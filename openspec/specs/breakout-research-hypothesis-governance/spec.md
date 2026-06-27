# breakout-research-hypothesis-governance Specification

## Purpose
Define the governance contract for autonomous BTCUSDT breakout research cycles so they select bounded hypotheses from local evidence, preserve the quarterly 2023q1-2024q4 `8/8` target, and stop only on measured success or an explicit external blocker.
## Requirements
### Requirement: Research loop discovers the current bounded hypothesis before stopping
The system SHALL define a bounded local discovery step for selecting the next breakout research hypothesis before an autonomous research cycle reports that no local tasks exist.

#### Scenario: Active change exists
- **WHEN** one or more active OpenSpec changes exist
- **THEN** the research loop selects the active change that is already started or most directly tied to the current owner goal
- **AND** it does not start a new hypothesis unless the active work is blocked or outside the owner goal

#### Scenario: No active change exists but local evidence contains a next hypothesis
- **WHEN** no active OpenSpec change exists
- **AND** current specs, archived recommendations, docs, tests, code comments, or diagnostic artifacts identify a bounded unresolved breakout hypothesis
- **THEN** the research loop treats that hypothesis as a local task
- **AND** creates exactly one narrow OpenSpec change for that hypothesis before implementation

#### Scenario: No bounded hypothesis is found
- **WHEN** active changes, current specs, archived recommendations, docs, tests, code comments, and diagnostic artifacts do not identify a bounded unresolved hypothesis
- **THEN** the research loop may report that local tasks are absent
- **AND** the report includes which local sources were checked

### Requirement: BTCUSDT research uses an eight-quarter scorecard
The system SHALL require every selected BTCUSDT breakout research hypothesis to define an explicit eight-quarter scorecard before source implementation. For this research line, `8/8` means all eight quarterly windows from 2023q1 through 2024q4 pass configured research thresholds.

#### Scenario: Exposure-scaled profile scorecard is created
- **WHEN** an exposure-scaled exit/path-risk profile is selected
- **THEN** the scorecard contains exactly these windows: `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, and `2024q4`
- **AND** each quarter has one of the statuses `pass`, `fail`, `unknown`, or `blocked`
- **AND** each quarter identifies the command, artifact, metric, blocker, or review evidence needed to verify it
- **AND** changing fixed candidate exposure SHALL NOT weaken `min_trade_count`, `min_net_profit`, `min_profit_factor`, `min_max_drawdown`, feed-gap requirements, realistic-cost requirements, or quarter coverage.

### Requirement: Research iterations target the highest-impact failing quarter or shared mechanism
The system SHALL drive each research iteration toward the failing quarter or shared failure mechanism that most directly prevents quarterly `8/8`.

#### Scenario: Iteration begins
- **WHEN** the quarterly scorecard contains one or more `fail`, `unknown`, or `blocked` quarters
- **THEN** the next implementation or research step targets one primary failing quarter or a shared mechanism across failing quarters
- **AND** the selected target is justified as the highest-impact blocker to reaching quarterly `8/8`

#### Scenario: Iteration completes
- **WHEN** a significant code, spec, test, data, or research change is completed
- **THEN** the quarterly scorecard is updated
- **AND** the report states whether the change moved the score toward quarterly `8/8`
- **AND** a non-improving direction is stopped or justified with new evidence

### Requirement: Archived research is negative evidence by default
The system SHALL treat archived research changes as evidence of prior attempts, blockers, and dead ends rather than as ready-made solutions.

#### Scenario: Archive is consulted
- **WHEN** archived changes are reviewed for a current hypothesis
- **THEN** the review identifies what was tried, which quarters or windows failed, why the method did not reach quarterly `8/8`, and which scopes were deferred
- **AND** it records useful constraints and failure modes

#### Scenario: Archived method is considered again
- **WHEN** a research loop proposes to reuse an archived method
- **THEN** it must identify which previous blocker is now absent or which new condition makes the method applicable
- **AND** it must verify that repeating the method does not lower the current hypothesis target

### Requirement: External research is bounded and locally validated
The system SHALL allow external research sources, including arXiv, only as bounded sources of ideas when local evidence and current implementation paths are insufficient.

#### Scenario: Subagents research alternatives
- **WHEN** progress stalls or two consecutive iterations do not move the quarterly scorecard toward `8/8`
- **THEN** research-only subagents may inspect local specs, archives, docs, tests, code, and artifacts
- **AND** they return facts, checked dead ends, candidate alternatives, risks, and file paths
- **AND** they do not modify the working tree

#### Scenario: arXiv idea is considered
- **WHEN** an arXiv paper or external research idea is used
- **THEN** the research loop records the paper title or arXiv identifier
- **AND** maps the idea to local specs, data availability, tests, metrics, and safety constraints
- **AND** rejects paper-driven complexity when a simpler local path can reach quarterly `8/8`

### Requirement: Research stop conditions are explicit
The system SHALL stop a research cycle only with either an `8/8` quarterly scorecard or a documented external blocker.

#### Scenario: Hypothesis reaches success
- **WHEN** all eight quarterly windows are `pass`
- **AND** required verification commands or artifacts are recorded
- **AND** OpenSpec validation passes
- **THEN** the cycle may stop with success
- **AND** no additional cleanup, refactor, or new hypothesis is started in the same cycle
- **AND** a Telegram success notification is sent or the send failure is recorded in the final report

#### Scenario: Telegram success notification is sent
- **WHEN** the BTCUSDT quarterly scorecard reaches `8/8`
- **THEN** the notification includes the change id, profile or hypothesis name, passed quarters, key research thresholds or metrics, artifact or summary paths, local commit hash when available, and local-only delivery confirmation
- **AND** the notification does not include secrets, tokens, private values, private account data, or large logs

#### Scenario: Hypothesis is externally blocked
- **WHEN** one or more quarterly windows cannot be evaluated or fixed locally
- **THEN** the cycle may stop with a blocker only after recording the missing data, access, command, owner decision, or external dependency
- **AND** the report includes what was checked and why local work cannot proceed safely

### Requirement: BTCUSDT research success uses net-of-costs robustness verdicts
The BTCUSDT breakout research loop SHALL treat `8/8` after realistic costs as the success condition for robustness-search changes. Baseline-only `8/8` SHALL be insufficient and SHALL NOT stop the loop as a successful profile.

#### Scenario: Baseline-only 8/8 appears
- **WHEN** a candidate reaches `8/8` only under baseline or legacy costs
- **AND** fails one or more required quarters under realistic costs
- **THEN** the research loop records the baseline result as insufficient
- **AND** archives the candidate as falsified robustness evidence when the change closes
- **AND** continues to the next bounded hypothesis unless an external blocker prevents safe local work.

#### Scenario: Net-of-costs 8/8 appears
- **WHEN** a candidate reaches `8/8` under realistic costs using the required quarterly windows and thresholds
- **THEN** the research loop may stop with success for the research slice
- **AND** the final report states `successful profile = 8/8 after realistic costs`.

### Requirement: Telegram success notifications are gated by realistic-cost success
The BTCUSDT breakout research loop SHALL send a Telegram success notification only for a candidate that reaches `8/8` after realistic costs, not for baseline-only `8/8`.

#### Scenario: Baseline-only profile passes
- **WHEN** a candidate reaches baseline-only `8/8`
- **THEN** no Telegram success notification is sent
- **AND** the final report records that notification was intentionally withheld because baseline-only `8/8` is insufficient.

#### Scenario: Realistic-cost profile passes
- **WHEN** a candidate reaches `8/8` after realistic costs
- **THEN** a Telegram success notification is sent or the send failure is recorded
- **AND** the notification includes the change id, profile name, realistic cost settings, passed quarters, thresholds, summary artifact paths, and no secrets or private account data.

