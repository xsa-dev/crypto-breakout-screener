## ADDED Requirements

### Requirement: Backtests use the online information boundary
The backtest engine SHALL evaluate historical bars/ticks using only information available at each simulated timestamp and SHALL reuse the same level/setup/state/risk logic as online evaluation.

#### Scenario: Future data is unavailable during simulation
- **WHEN** a backtest evaluates a signal at bar N
- **THEN** the strategy cannot inspect bars after N except for explicitly delayed confirmation that would also be unavailable live

### Requirement: Reports are reproducible artifacts
The reporting layer SHALL produce deterministic report artifacts with config hash, dataset hash, parameter snapshot, trade list, scenario breakdown, score distribution, false-breakout analysis, slippage assumptions, equity, drawdown, and return distribution.

#### Scenario: Report links to run metadata
- **WHEN** a backtest report is generated
- **THEN** it includes or references the backtest run id, config hash, dataset hash, time range, and exported artifact paths
