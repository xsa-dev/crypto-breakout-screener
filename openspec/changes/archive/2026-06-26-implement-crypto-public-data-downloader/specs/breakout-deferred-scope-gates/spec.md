## ADDED Requirements
### Requirement: Public downloader cannot access private trading scope
The BTCUSDT public data downloader SHALL remain unauthenticated and read-only. It SHALL NOT read private API credentials, set authorization headers, call private endpoints, submit/cancel/modify/query orders, query account balances, query positions, or reconcile broker state.

#### Scenario: Private credentials are present in the environment
- **WHEN** fake or real private exchange environment variables are present while running the public downloader
- **THEN** the downloader behavior is unchanged
- **AND** no private values appear in downloaded CSV, source metadata, manifest, report JSON, logs, or command summary

#### Scenario: Implementation attempts private endpoint access
- **WHEN** downloader implementation attempts to import `src.core.env`, read `.env`, sign requests, add authorization headers, or call private exchange/account endpoints
- **THEN** the work is out of scope for this change
- **AND** a separate reviewed OpenSpec change is required before implementation can continue
