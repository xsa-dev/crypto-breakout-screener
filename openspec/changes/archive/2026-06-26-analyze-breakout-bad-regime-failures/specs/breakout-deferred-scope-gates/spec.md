# breakout-deferred-scope-gates Specification Delta

## ADDED Requirements
### Requirement: Bad-regime diagnostics do not approve new filters or production trading
Bad-regime diagnostics SHALL be research evidence only and SHALL NOT by themselves approve a new trading filter, live trading, full-auto production behavior, or private exchange access.

#### Scenario: Diagnostics reveal a promising regime bucket
- **WHEN** diagnostics identify a bucket with poor expectancy or high drawdown contribution
- **THEN** the bucket is reported as a candidate hypothesis for a later reviewed change
- **AND** implementation of a new entry/no-trade filter remains out of scope unless separately approved by OpenSpec
