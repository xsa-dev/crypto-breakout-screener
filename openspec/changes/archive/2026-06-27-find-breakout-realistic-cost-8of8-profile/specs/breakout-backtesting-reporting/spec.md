## ADDED Requirements

### Requirement: Realistic-cost breakout profile search uses fixed eight-quarter gates
The BTCUSDT breakout research runner SHALL evaluate robust profile-search candidates against exactly the eight quarterly windows `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, and `2024q4`, using unchanged research thresholds: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, and `require_no_feed_gaps=true`.

#### Scenario: Candidate scorecard is produced
- **WHEN** a robust breakout profile candidate is evaluated
- **THEN** the scorecard includes exactly `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, and `2024q4`
- **AND** the summary records the unchanged thresholds
- **AND** no missing or removed quarter can be counted as a pass
- **AND** each quarter records pass/fail status and blockers.

#### Scenario: Threshold weakening is attempted
- **WHEN** a candidate run lowers `min_trade_count`, `min_net_profit`, `min_profit_factor`, or `min_max_drawdown`, or disables `require_no_feed_gaps`
- **THEN** the run is marked non-acceptance research output
- **AND** it cannot produce a successful profile verdict.

### Requirement: Successful breakout profiles require realistic costs
The BTCUSDT breakout research verdict SHALL treat a profile as successful only when all eight required quarters pass after realistic costs, including notional `commission_rate=0.00055` per side, stressed spread/slippage, and conservative `funding_rate_per_bar > 0`.

#### Scenario: Profile passes after realistic costs
- **WHEN** a candidate profile passes all eight required quarters under realistic costs
- **THEN** the summary marks the candidate classification as `net_costs_supported`
- **AND** records `successful profile = 8/8 after realistic costs`
- **AND** records cost model settings, aggregate metrics, per-quarter metrics, blockers, and artifact paths.

#### Scenario: Profile passes baseline only
- **WHEN** a candidate profile passes all eight quarters under baseline or legacy costs
- **AND** the same candidate fails one or more required quarters under realistic costs
- **THEN** the summary marks baseline `8/8` as insufficient
- **AND** classifies the candidate as `falsified_realistic_costs`
- **AND** records the failed realistic-cost quarters and blockers as robustness evidence.

#### Scenario: Realistic cost settings are missing
- **WHEN** a candidate has no run or artifact proving `commission_rate=0.00055` per side, stressed spread/slippage, and `funding_rate_per_bar > 0`
- **THEN** the candidate cannot be classified as successful
- **AND** the blocker identifies the missing cost setting or missing artifact.

### Requirement: Robust profile artifacts are complete for every candidate
Every robust profile-search candidate SHALL produce deterministic artifacts that make baseline and realistic-cost verdicts auditable without manually reconstructing runs.

#### Scenario: Candidate artifacts are written
- **WHEN** a candidate evaluation completes or is falsified
- **THEN** its artifact directory includes `summary.json`
- **AND** includes `scorecard.csv`
- **AND** includes serialized `cost_model_settings` for baseline and realistic/stress runs
- **AND** records per-quarter pass/fail status, trade count, net profit, profit factor, max drawdown, feed gap status, blockers, and referenced run artifact paths.

#### Scenario: Candidate classification is reviewed
- **WHEN** a reviewer opens `summary.json`
- **THEN** it states one of `net_costs_supported`, `baseline_only_insufficient`, `falsified_realistic_costs`, `technical_blocked`, or `not_supported`
- **AND** the classification is traceable to the scorecard and cost settings.

### Requirement: Robust search moves away from cost-sensitive turnover
The robust profile search SHALL prioritize fixed, named profiles that reduce cost sensitivity versus the falsified tight ATR profile by limiting turnover and improving gross edge per trade.

#### Scenario: Candidate profile is defined
- **WHEN** a candidate profile is added to the search
- **THEN** its settings are named and serialized
- **AND** it documents how it attempts lower turnover, larger average trade, or stronger gross edge per trade through bounded controls such as cooldown, max trades, regime filters, or exit horizon
- **AND** it does not rely on broad unconstrained parameter search.

#### Scenario: High-turnover tight profile is used as reference
- **WHEN** a microscopic tight-stop, one-bar, or high-turnover profile is included
- **THEN** it is labelled as reference or negative robustness evidence unless it also passes the required realistic-cost `8/8` gate.
