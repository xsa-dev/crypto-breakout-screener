# breakout-deferred-scope-gates Specification Delta

## ADDED Requirements
### Requirement: Breakout confirmation comparison is research-only
Breakout confirmation comparison SHALL be treated as local historical research and SHALL NOT approve production trading.

#### Scenario: A confirmation profile improves results
- **WHEN** a confirmation profile improves quarterly research metrics or reaches `hypothesis_supported=true`
- **THEN** the result is research evidence only
- **AND** live trading, production approval, private exchange access, and automated deployment remain out of scope.

### Requirement: Confirmation comparison does not introduce ML or microstructure scope
Breakout confirmation comparison SHALL remain deterministic and OHLCV-based.

#### Scenario: A future idea needs ML or order-flow data
- **WHEN** a future proposal needs ML, boosting, neural networks, LLM trading decisions, order book, стакан, DOM, L2 depth, footprint, taker-flow, or trade tape data
- **THEN** it must be a separate OpenSpec change with explicit data availability, no-lookahead, storage, and artifact requirements.
