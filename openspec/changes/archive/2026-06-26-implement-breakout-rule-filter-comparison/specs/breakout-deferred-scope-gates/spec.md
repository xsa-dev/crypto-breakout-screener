# breakout-deferred-scope-gates Specification Delta

## ADDED Requirements
### Requirement: Feature-filter comparison does not approve production trading
Research feature-filter comparison SHALL remain a local diagnostic/backtest activity. It SHALL NOT enable production OOS approval, live broker execution, private exchange access, full-auto trading, ML training, optimization search, or deployment behavior.

#### Scenario: Feature-filter profile improves research metrics
- **WHEN** a feature-filter profile improves quarterly passed-window count, drawdown, profit factor, or net profit
- **THEN** the result is recorded as research evidence only
- **AND** live trading, production full-auto behavior, broker adapters, and production approval remain blocked until later reviewed OpenSpec changes

#### Scenario: Implementation attempts optimization or ML
- **WHEN** the implementation proposes automatic threshold search, model training, boosting, neural networks, or model inference for this change
- **THEN** the work is out of scope
- **AND** implementation must stop until a separate reviewed OpenSpec change approves ML or optimization research
