## ADDED Requirements

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
