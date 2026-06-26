## ADDED Requirements
### Requirement: Crypto batch runner cannot access private trading scope
The BTCUSDT batch experiment runner SHALL remain unauthenticated and read-only. It SHALL NOT read private API credentials, set authorization headers, call private endpoints, submit/cancel/modify/query orders, query account balances, query positions, reconcile broker state, or enable live trading.

#### Scenario: Private credentials are present during a batch run
- **WHEN** fake or real private exchange environment variables are present while running the batch runner
- **THEN** the batch runner behavior is unchanged
- **AND** no private values appear in downloaded CSV files, per-window manifests, batch summary CSV/JSON, logs, or command summary

#### Scenario: Batch implementation attempts private or production scope
- **WHEN** implementation attempts to import `src.core.env`, read `.env`, sign requests, add authorization headers, call private exchange/account endpoints, add live execution, or claim production approval
- **THEN** the work is out of scope for this change
- **AND** a separate reviewed OpenSpec change is required before implementation can continue
