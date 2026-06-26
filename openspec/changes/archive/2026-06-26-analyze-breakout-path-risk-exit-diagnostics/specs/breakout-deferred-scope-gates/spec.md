# breakout-deferred-scope-gates Specification Delta

## ADDED Requirements
### Requirement: Path-risk diagnostics do not approve exit-rule changes
Path-risk diagnostics SHALL be research-only and SHALL NOT by themselves approve production, live trading, full automation, or exit-rule implementation.

#### Scenario: Exit-rule implementation remains deferred
- **GIVEN** path-risk diagnostics identify a potentially favorable stop, trailing, break-even, or holding behavior
- **WHEN** the diagnostic change is complete
- **THEN** no stop-loss, take-profit, trailing-stop, break-even, holding, or position-management rule is added by this change
- **AND** any implementation of such behavior requires a separate approved OpenSpec change.

### Requirement: Path-risk diagnostics do not add new data dimensions
Path-risk diagnostics SHALL NOT introduce order book, стакан, DOM, L2, footprint, taker-flow, trade tape, private API, or new symbol/timeframe scope.

#### Scenario: Richer market microstructure remains deferred
- **GIVEN** a path-risk question could benefit from order book or execution-flow data
- **WHEN** this diagnostic change is implemented
- **THEN** the implementation remains scoped to public OHLCV and already-produced trade metadata
- **AND** any order book or execution-flow research requires a separate approved OpenSpec change.
