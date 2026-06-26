# breakout-deferred-scope-gates Specification Delta

## ADDED Requirements
### Requirement: Drawdown risk-control comparison does not approve production trading
Research drawdown risk-control comparison SHALL remain local diagnostic/backtest work. It SHALL NOT enable production OOS approval, live broker execution, private exchange access, full-auto trading, ML training, optimization search, deployment, or UI behavior.

#### Scenario: Risk-control profile improves research metrics
- **WHEN** a drawdown risk-control profile improves passed-window count, drawdown, profit factor, or net profit
- **THEN** the result is recorded as research evidence only
- **AND** live trading, production full-auto behavior, broker adapters, and production approval remain blocked until later reviewed OpenSpec changes

#### Scenario: Implementation attempts optimization search
- **WHEN** the implementation proposes arbitrary parameter search, grid search, Bayesian optimization, ML training, boosting, neural networks, or model inference for this change
- **THEN** the work is out of scope
- **AND** implementation must stop until a separate reviewed OpenSpec change approves that research scope
