# breakout-deferred-scope-gates Specification Delta

## ADDED Requirements
### Requirement: Forward-path diagnostics do not approve exit-rule changes
Forward-path and MAE/MFE diagnostics SHALL be research evidence only and SHALL NOT by themselves implement or approve new holding, stop, take-profit, trailing-stop, or exit rules.

#### Scenario: Diagnostics suggest a better holding horizon
- **WHEN** forward-path diagnostics suggest that a different holding horizon, trailing exit, stop, or take-profit may improve results
- **THEN** the result is recorded as candidate evidence for a later reviewed OpenSpec change
- **AND** source changes that alter live or backtest exit behavior remain out of scope until separately approved

### Requirement: Forward-path diagnostics do not approve production trading
Forward-path diagnostics SHALL NOT enable production OOS approval, live broker execution, private exchange access, full-auto trading, ML training, optimization search, deployment, or UI behavior.

#### Scenario: Forward-path diagnostics look favorable
- **WHEN** forward-path diagnostics show favorable MFE, synthetic horizon PnL, or passed-vs-failed separation
- **THEN** the output remains research-only
- **AND** live trading, production full-auto behavior, broker adapters, and production approval remain blocked until later reviewed OpenSpec changes
