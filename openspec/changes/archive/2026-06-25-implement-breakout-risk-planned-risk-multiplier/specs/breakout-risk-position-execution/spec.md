## MODIFIED Requirements

### Requirement: Position size is derived from risk and stop distance
The system SHALL calculate position size using configured risk, equity, stop distance, and instrument multiplier. Baseline formula is `floor((equity * risk_pct) / stop_distance_money)` where `stop_distance_money = abs(entry_price - stop_price) * contract_multiplier`. Approved trade decisions SHALL report `planned_risk` using the same stop-distance money formula so approval audit data matches the risk-derived quantity.

#### Scenario: Position size is calculated
- **WHEN** equity, risk percent, entry, stop, and contract multiplier are known
- **THEN** Risk Manager calculates maximum allowed position size before execution
- **AND** the approved decision records multiplier-aware planned risk for the approved quantity

#### Scenario: Stop distance is invalid
- **WHEN** stop distance is zero, negative, or too small for instrument constraints
- **THEN** Risk Manager rejects the trade intent
