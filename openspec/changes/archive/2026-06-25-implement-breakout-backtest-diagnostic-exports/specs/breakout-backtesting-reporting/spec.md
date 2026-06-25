## MODIFIED Requirements
### Requirement: Reports are reproducible artifacts
The reporting layer SHALL produce deterministic report artifacts with config hash, dataset hash, parameter snapshot, trade list, scenario breakdown, score distribution, false-breakout analysis, slippage assumptions, equity, drawdown, and return distribution. Local report export SHALL materialize these diagnostics as separate deterministic artifacts, or record explicit unavailable reasons for unsupported optional formats.

#### Scenario: Report links to run metadata
- **WHEN** a backtest report is generated
- **THEN** it includes or references the backtest run id, config hash, dataset hash, time range, and exported artifact paths

#### Scenario: Diagnostic artifacts are exported
- **WHEN** a completed report is exported locally
- **THEN** artifact paths include the full report, trade list, equity curve, drawdown curve, return distribution, metrics, scenario breakdown, score distribution, false-breakout analysis, slippage report, and parameter snapshot
- **AND** repeated exports of the same report produce stable artifact names and content
