# breakout-deferred-scope-gates Specification Delta

## ADDED Requirements
### Requirement: Volatility-regime filter comparison is research-only
Volatility/no-trade regime filter comparison SHALL be treated as deterministic research evidence only and SHALL NOT approve production full-auto trading.

#### Scenario: Regime-filter profile improves quarterly results
- **WHEN** a volatility-regime profile improves pass count, drawdown, net profit, or hypothesis support status
- **THEN** the result remains research-only
- **AND** no live trading, full-auto production mode, private API, concrete exchange adapter, order placement, balance query, or position query is approved by this change

### Requirement: Volatility-regime comparison excludes learned optimization
This change SHALL compare only the fixed profile set described in the OpenSpec design.

#### Scenario: Additional thresholds are proposed during implementation
- **WHEN** implementation discovers a tempting new threshold, grid-search range, Bayesian optimization, ML, boosting, or neural-network classifier
- **THEN** it is out of scope
- **AND** it requires a separate OpenSpec change before implementation
