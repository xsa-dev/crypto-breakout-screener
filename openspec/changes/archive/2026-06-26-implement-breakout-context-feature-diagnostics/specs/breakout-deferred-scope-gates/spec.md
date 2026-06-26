## ADDED Requirements
### Requirement: Feature diagnostics do not enable model-training or live-trading scope
Feature diagnostics SHALL remain a local explainability layer. They SHALL NOT enable ML model training, threshold optimization, private data access, broker execution, live trading, production OOS approval, or full-auto trading.

#### Scenario: User asks for neural networks or boosting before diagnostic evidence exists
- **WHEN** feature diagnostics have not yet produced audited feature/regime evidence
- **THEN** neural-network, boosting, and automated model-filter implementation remains deferred to a separate OpenSpec change
- **AND** this change may only recommend candidate ML/filter directions based on diagnostic artifacts

#### Scenario: Private credentials exist during feature diagnostics
- **WHEN** fake or real private exchange environment variables are present while running feature diagnostics
- **THEN** feature diagnostics and batch commands do not read, require, print, or persist those secrets
- **AND** no private endpoints, account data, balances, positions, orders, or broker adapters are used
