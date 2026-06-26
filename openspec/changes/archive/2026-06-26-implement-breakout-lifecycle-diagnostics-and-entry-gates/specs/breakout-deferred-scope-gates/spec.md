## ADDED Requirements
### Requirement: Lifecycle diagnostics and research gates do not enable private or live trading scope
Lifecycle diagnostics and gated research runs SHALL remain local, unauthenticated, and read-only. They SHALL NOT enable private exchange endpoints, broker adapters, order placement, live position reconciliation, production OOS approval, or full-auto trading.

#### Scenario: Gated research appears profitable
- **WHEN** lifecycle gates reduce trade count, reduce drawdown, or improve batch profitability
- **THEN** the result is still marked research-only
- **AND** production/live/full-auto approval remains blocked by existing deferred-scope gates

#### Scenario: Secrets are present in the environment
- **WHEN** environment variables or local credential files exist on the developer machine
- **THEN** lifecycle diagnostics and gated batch commands do not read, require, print, or persist those secrets
