# breakout-backtesting-reporting Specification Delta

## ADDED Requirements
### Requirement: Backtests export path-risk diagnostics
Backtest report export SHALL support deterministic path-risk diagnostics for already-produced trades when path-risk diagnostics are explicitly enabled.

#### Scenario: Path-risk diagnostics are exported as separate artifacts
- **GIVEN** a completed backtest report with trades and path-risk diagnostics enabled
- **WHEN** report artifacts are exported
- **THEN** the export includes a per-run `*-path-risk-diagnostics.csv`
- **AND** the export includes a per-run `*-path-risk-threshold-summary.csv`
- **AND** these artifacts are referenced in the report artifact paths
- **AND** actual realized metric artifacts remain unchanged.

#### Scenario: Batch path-risk summaries are exported separately
- **GIVEN** a batch run with path-risk diagnostics enabled
- **WHEN** the batch summary is written
- **THEN** the batch output includes `path-risk-window-summary.csv`
- **AND** the batch output includes `passed-vs-failed-path-risk-summary.csv`
- **AND** the batch summary JSON references those diagnostic artifact paths.

#### Scenario: Path-risk diagnostics preserve actual metrics
- **GIVEN** the same input data and strategy configuration
- **WHEN** path-risk diagnostics are enabled versus disabled
- **THEN** trade selection, actual realized metrics, and batch verdicts are identical
- **AND** path-risk feasibility labels are not reported as actual strategy results.

### Requirement: Path-risk diagnostics expose threshold ordering fields
Path-risk diagnostic artifacts SHALL include enough fields to compare favorable and adverse excursion ordering without implementing new exits.

#### Scenario: Threshold ordering fields are present
- **GIVEN** path-risk diagnostics for a trade with entry-time ATR available
- **WHEN** fixed favorable and adverse ATR thresholds are evaluated
- **THEN** the diagnostic row includes first favorable threshold hit, first adverse threshold hit, hit bar offsets, favorable-before-adverse labels, adverse-before-favorable labels, break-even reachability labels, break-even touch-after-reach labels, and fixed trailing giveback touch labels
- **AND** break-even reachability is defined as first reaching `+1.0 ATR` from entry inside the horizon
- **AND** trailing giveback labels use fixed `0.5 ATR` and `1.0 ATR` giveback levels below the maximum high observed after a favorable threshold was reached
- **AND** the labels are computed only from bars inside the configured horizon.
