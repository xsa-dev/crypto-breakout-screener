## ADDED Requirements

### Requirement: BTCUSDT batch stress tests record realistic cost assumptions
The BTCUSDT batch runner SHALL support explicit stress-test cost assumptions for spread, slippage, commission, and funding, including notional commission and funding rates, and SHALL record those assumptions in deterministic batch artifacts.

#### Scenario: Stress run uses explicit notional costs
- **WHEN** the BTCUSDT batch runner is executed with non-zero notional commission or funding rates
- **THEN** each backtest window includes those costs in trade `total_cost` and `net_pnl`
- **AND** the batch summary JSON and CSV record the cost model settings used
- **AND** cached public market-data CSVs can be reused without network access when explicitly requested

#### Scenario: Tight ATR profile is stress-tested
- **WHEN** the `conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p01-target-2p0` profile is rerun over `2023q1..2024q4` under explicit stress cost assumptions
- **THEN** the output records per-quarter pass/fail status, blockers, trade count, net profit, max drawdown, profit factor, cost settings, and artifact paths
- **AND** the result is reported as research robustness evidence only, not production approval

#### Scenario: Ledger-level cost stress is used as negative robustness evidence
- **WHEN** exact quarterly reruns are too slow for an interactive loop
- **THEN** a separately labelled ledger-level stress artifact MAY preserve original entries/exits and subtract additional costs per realized trade
- **AND** the artifact SHALL NOT be described as an exact cost-dependent signal rerun
