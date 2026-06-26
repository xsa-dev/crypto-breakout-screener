# breakout-backtesting-reporting Specification Delta

## ADDED Requirements
### Requirement: Backtests support research-only drawdown risk-control profiles
The backtest runtime SHALL support disabled-by-default research risk-control profiles that can reduce drawdown concentration on top of explicit feature-filter profiles. These controls SHALL use only realized trade state and entry-time information available before a new trade is created.

#### Scenario: Risk controls are disabled by default
- **WHEN** a backtest runs without a drawdown risk-control profile
- **THEN** baseline, conservative lifecycle, and committed feature-filter profile behavior remains unchanged
- **AND** risk-control skip/pause counters are empty or zero

#### Scenario: Daily stop profile is applied
- **WHEN** a named research profile configures a stricter daily stop loss
- **THEN** entries after the stop is reached are skipped with a deterministic reason
- **AND** realized PnL is attributed to the trade exit UTC day

#### Scenario: Loss-cooldown profile is applied
- **WHEN** a named research profile configures a longer cooldown after loss
- **THEN** entries after realized losing trades are skipped until the configured cooldown has elapsed
- **AND** skip counts identify the cooldown reason

### Requirement: Batch summaries compare drawdown risk-control profiles
BTCUSDT batch summaries SHALL make drawdown risk-control comparisons auditable across the quarterly 2023-2024 windows.

#### Scenario: Risk-control profile batch completes
- **WHEN** a quarterly batch runs with a named drawdown risk-control profile
- **THEN** every summary window records the profile name, serialized settings, skip/pause counts, and artifact paths
- **AND** the aggregate summary records trade count, net profit, worst max drawdown, profit factor, passed-window count, failed-window count, blockers, and hypothesis verdict

#### Scenario: Worst-day evidence is reviewed
- **WHEN** a risk-control profile still fails one or more windows
- **THEN** the summary or referenced artifacts identify worst-day attribution for the failed windows
- **AND** the review can compare whether failures are broad-window degradation or concentrated worst-day drawdown
