## ADDED Requirements

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
