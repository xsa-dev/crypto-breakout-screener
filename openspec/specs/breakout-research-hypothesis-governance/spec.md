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

### Requirement: Altcoin universe research preserves per-symbol audit evidence
The crypto breakout research loop SHALL record per-symbol evidence for approved-symbol universe hypotheses. Per-symbol results SHALL be used for smoke checks, contribution analysis, blockers, and auditability; shared-bankroll portfolio hypotheses SHALL determine `8/8` success from the combined portfolio scorecard rather than from independent per-symbol deposits.

#### Scenario: ETHUSDT universe hypothesis is selected
- **WHEN** ETHUSDT is selected as the next crypto research symbol
- **THEN** the research loop defines the same required windows `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, and `2024q4`
- **AND** the ETHUSDT-only run may be used as data proof, smoke evidence, or standalone single-symbol research evidence
- **AND** ETHUSDT-only success SHALL NOT be counted as shared-bankroll portfolio success unless the active hypothesis is explicitly single-symbol
- **AND** BTCUSDT negative evidence remains archived and is not counted as ETHUSDT success or failure.

#### Scenario: Fifty-symbol universe smoke is evaluated
- **WHEN** the fixed 50-symbol altcoin allowlist is used for smoke/early-falsification research
- **THEN** each symbol/profile result records symbol, profile, evaluated required quarter, metrics, blockers, and artifact paths
- **AND** a symbol/profile candidate may be promoted to a full eight-quarter scorecard only if its smoke result does not fail the selected blocker quarter
- **AND** unavailable public history, provider absence, or insufficient data is recorded as blocked evidence for that exact symbol
- **AND** failed symbols are archived as negative evidence rather than averaged with other symbols.

#### Scenario: Altcoin profile reaches success
- **WHEN** the active hypothesis is single-symbol and one approved symbol/profile pair reaches `8/8` under realistic costs using the required quarterly windows and thresholds
- **THEN** the research loop may stop with success for that symbol/profile pair
- **AND** the final report states the successful symbol, profile, realistic-cost settings, passed quarters, and artifact paths
- **AND** when the active hypothesis is shared-bankroll portfolio research, this per-symbol result remains contribution evidence rather than final portfolio success.

### Requirement: Altcoin universe portfolio research uses one shared bankroll
The crypto breakout research loop SHALL evaluate broad altcoin-universe candidates as one shared-bankroll portfolio when the hypothesis targets a multi-symbol scope. The portfolio SHALL start each required quarterly window with `10000 USDT` and SHALL NOT assign independent deposits to each symbol.

#### Scenario: Portfolio universe hypothesis is selected
- **WHEN** a 50-symbol altcoin universe portfolio hypothesis is selected
- **THEN** each required quarterly scorecard uses one shared starting equity of `10000 USDT`
- **AND** all symbol trades in that quarter update one combined portfolio equity curve
- **AND** per-trade notional, total open exposure, cash usage, and rejected-over-cap signals are recorded
- **AND** portfolio success is evaluated in money terms after realistic costs.

#### Scenario: Portfolio quarter is scored
- **WHEN** a shared-bankroll portfolio quarter is scored
- **THEN** `min_net_profit=0.0` applies to total portfolio net profit in USDT
- **AND** `min_profit_factor=1.0` applies to the combined closed-trade portfolio ledger
- **AND** `min_max_drawdown=-0.35` applies to the combined portfolio equity curve relative to `10000 USDT`
- **AND** per-symbol contribution tables are recorded without allowing one symbol to hide missing data or unsupported scope.

#### Scenario: Portfolio profile reaches success with buffer
- **WHEN** one shared-bankroll portfolio profile reaches `8/8` under realistic costs
- **THEN** the final report includes threshold-distance buffers for net profit, profit factor, and max drawdown in each quarter
- **AND** the success notification is sent only after portfolio artifacts show all eight quarters passed with the shared `10000 USDT` bankroll.

### Requirement: Portfolio research labels long, short-or-avoid, and ambiguous regimes
The crypto breakout research loop SHALL classify deterministic market regimes for promoted portfolio hypotheses before claiming a portfolio `8/8` result. Regime labels SHALL distinguish long-enabled bullish conditions from bearish conditions that require short-side research or risk-off blocking, and from ambiguous conditions that cannot be counted as validated edge.

#### Scenario: Regime labels are produced
- **WHEN** a shared-bankroll portfolio profile is promoted beyond smoke evaluation
- **THEN** each evaluated trade opportunity or scoring interval is assigned one of `bull_long`, `bear_short_or_avoid`, or `neutral_blocked`
- **AND** the label is derived from deterministic public OHLCV context already available to the runner
- **AND** the summary records which labels permit long entries, which labels require short-side research or risk-off treatment, and which labels are blocked.

#### Scenario: Bearish regime lacks short implementation
- **WHEN** a scoring interval is labeled `bear_short_or_avoid` and no explicit short-side execution model is implemented
- **THEN** the long breakout runner treats that interval as avoid/risk-off evidence
- **AND** it does not count skipped bearish intervals as long-edge success
- **AND** it records skipped or blocked signals in the per-regime report.

#### Scenario: Portfolio quarter is reported by regime
- **WHEN** a portfolio quarter is scored
- **THEN** the report includes per-regime trade count, PnL contribution, drawdown contribution, skipped/blocked signal count, and artifact paths
- **AND** a portfolio `8/8` pass is not accepted if bear or ambiguous intervals are silently averaged into the long bucket without explicit regime rules.

### Requirement: Breakout research implements the supplied screener documentation
The breakout research loop SHALL treat `doc/ai/task` as the primary algorithmic source for the screener/trading-system strategy and SHALL NOT replace it with unrelated strategy invention.

#### Scenario: Implementation change is created
- **WHEN** a breakout implementation OpenSpec change is proposed
- **THEN** it identifies which source-document algorithm block it implements, such as level search, setup score, entry mode, confirmation, retest, additions, false breakout, exit, risk management, or reporting
- **AND** any deviation from the source documentation is recorded as a bounded implementation constraint rather than an invented strategy.

#### Scenario: Historical evidence is classified
- **WHEN** a backtest, smoke run, or promoted scorecard is reported
- **THEN** the report classifies evidence as `concept_evidence`, `friction_light_evidence`, `realistic_cost_evidence`, or `falsified_or_blocked_evidence`
- **AND** records universe, windows, cost assumptions, thresholds, and artifact paths.

#### Scenario: Friction-light 8/8 exists
- **WHEN** historical runs show `8/8` under favorable or missing execution costs
- **THEN** the result is preserved as positive concept evidence for the documented screener
- **AND** it is not claimed as realistic-cost production robustness unless realistic costs were included.

#### Scenario: Realistic-cost run fails
- **WHEN** a realistic-cost shared-bankroll run fails to reach `8/8`
- **THEN** the result is recorded as robustness/execution-cost evidence for that implementation profile
- **AND** it does not by itself invalidate the full documented screener when documented blocks remain unimplemented.

### Requirement: Portfolio cost-feasibility selection preserves the shared-bankroll success target
The crypto breakout research loop SHALL allow a deterministic, opt-in cost-feasibility selection profile for shared-bankroll altcoin portfolio hypotheses without weakening the fixed universe, realistic costs, configured thresholds, or required quarterly scorecard.

#### Scenario: Cost-feasibility profile is selected
- **WHEN** a shared-bankroll portfolio run selects `cost-feasible-v1`
- **THEN** the runner evaluates the approved fixed universe and required windows with one shared `10000 USDT` bankroll
- **AND** it keeps configured realistic spread, slippage, commission, funding, per-trade notional cap, total open-exposure cap, and research thresholds unchanged
- **AND** it skips long-enabled entries whose entry-time price/cost geometry is not feasible under the configured cost settings
- **AND** it records the skipped entries as blocked signals rather than deleting them from audit artifacts.

#### Scenario: Cost-feasibility profile is reported
- **WHEN** a portfolio scorecard is written for a run using a selection profile
- **THEN** the summary records `selection_profile`, `selection_settings`, and `selection_skip_counts`
- **AND** the per-regime report includes selection-skipped signals in skipped/blocked counts
- **AND** the trade ledger includes machine-readable selection blockers for skipped rows.

#### Scenario: Cost-feasibility profile reaches or fails portfolio success
- **WHEN** the cost-feasibility portfolio hypothesis is evaluated beyond smoke
- **THEN** success still requires all eight quarters `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, and `2024q4` to pass as one combined shared-bankroll portfolio under realistic costs with complete regime reporting and no missing feed gaps for the promoted universe run
- **AND** a result below `8/8` is recorded as falsified/negative evidence rather than success.
