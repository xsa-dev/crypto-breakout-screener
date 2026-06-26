# breakout-deferred-scope-gates Specification

## Purpose
Define non-negotiable guardrails that keep live broker execution, production full-auto behavior, concrete adapters, UI, backtesting runtime, and production operations out of scope until each deferred area receives its own reviewed OpenSpec change.
## Requirements
### Requirement: Deferred scopes require separate OpenSpec changes
The system SHALL treat live broker execution, full-auto production enablement, concrete live broker adapters, backtesting/reporting implementation, UI/operator dashboard implementation, and monitoring/ops/production hardening as deferred scopes. None of these scopes may be implemented under the foundation-only first GO unless a later OpenSpec change explicitly approves that scope.

#### Scenario: Foundation slice attempts deferred work
- **WHEN** an implementation task under the foundation-only first GO attempts to add live broker execution, full-auto production behavior, a concrete live adapter, backtesting/reporting runtime, UI dashboard, monitoring/ops runtime, or production hardening
- **THEN** the work is out of scope
- **AND** implementation must stop until a separate OpenSpec change is reviewed and approved

#### Scenario: Later change approves deferred work
- **WHEN** a later OpenSpec change explicitly scopes one deferred capability
- **THEN** only that named capability may be implemented
- **AND** unrelated deferred capabilities remain blocked

### Requirement: Live broker execution is blocked without an execution change
The system SHALL NOT submit, modify, cancel, or query live broker orders or positions until a dedicated execution OpenSpec change defines broker semantics, testnet/sandbox behavior, credentials handling, idempotency, reconciliation, rate limits, and verification.

#### Scenario: Live order code is proposed in foundation slice
- **WHEN** source changes add live order submission, cancellation, modification, or position synchronization against a real broker/API
- **THEN** the change is rejected as out of scope for the foundation slice

#### Scenario: Execution interface or fake adapter is proposed
- **WHEN** source changes add only broker-neutral interfaces, DTOs, or fake/test adapters required for contract tests
- **THEN** the work is allowed only if it has no live network side effects and no credential requirements

### Requirement: Full-auto mode remains non-production until separately approved
The system SHALL define `full_auto` as a supported mode contract, but production full-auto enablement SHALL remain blocked until a separate OpenSpec change defines production readiness gates, OOS thresholds, risk approvals, operator controls, rollback policy, and live-execution adapter scope. Local configuration validation SHALL fail closed for `full_auto` by default; any pre-approval opt-in SHALL be named as contract-validation-only rather than production approval.

#### Scenario: Config enables production full-auto before approval
- **WHEN** configuration attempts to enable production `full_auto` before a full-auto approval change exists
- **THEN** startup or mode activation is blocked with an explicit reason
- **AND** the reason identifies that a dedicated full-auto OpenSpec change is required

#### Scenario: Full-auto is used in tests
- **WHEN** tests exercise `full_auto` state transitions with fake adapters and no live side effects
- **THEN** the behavior is allowed as contract validation, not production approval
- **AND** the test must opt in through the explicit local contract-validation-only guard rather than changing the default production-safe behavior

### Requirement: Concrete live broker adapters are separate deliverables
The system SHALL NOT choose or implement a concrete live MT5, Bybit, exchange, broker, or terminal adapter in the foundation slice. Each live adapter SHALL have its own OpenSpec change covering API contract, order semantics, instrument metadata, time zones, rounding, rate limits, reconnect behavior, credential handling, and test environment.

#### Scenario: MT5 adapter is requested
- **WHEN** implementation proposes a MetaTrader 5 live adapter
- **THEN** it requires a dedicated MT5 adapter OpenSpec change before source implementation

#### Scenario: Bybit adapter is requested
- **WHEN** implementation proposes a Bybit live adapter
- **THEN** it requires a dedicated Bybit adapter OpenSpec change before source implementation

### Requirement: Backtesting and reporting runtime is deferred
The system SHALL specify backtesting/reporting requirements now, but implementation of the backtest engine, optimizer, report renderer, chart/export pipeline, and Monte Carlo runtime SHALL require a separate backtesting/reporting OpenSpec change after the foundation slice.

#### Scenario: Foundation code adds report generation
- **WHEN** implementation adds equity curves, drawdown charts, report exports, optimizer loops, walk-forward runtime, or Monte Carlo runtime during the foundation slice
- **THEN** the work is out of scope and must be moved to a later backtesting/reporting change

#### Scenario: Foundation code adds replay fixtures for no-lookahead
- **WHEN** implementation adds small deterministic replay fixtures only to test normalization, level detection, setup scoring, and no-lookahead behavior
- **THEN** the work is allowed as foundation verification, not a backtesting engine

### Requirement: UI/operator dashboard implementation is deferred
The system SHALL specify UI/operator MVP requirements now, but implementation of config editor, signal list, levels list, decision trace view, backtest run list, semi-auto confirm/reject controls, health/status pages, and operator dashboard endpoints SHALL require a separate UI/operator OpenSpec change.

#### Scenario: Foundation code adds dashboard routes
- **WHEN** implementation adds web routes, templates, frontend components, dashboard APIs, or manual confirmation controls during the foundation slice
- **THEN** the work is out of scope and must be moved to a later UI/operator change

#### Scenario: Foundation code defines DTOs consumed by future UI
- **WHEN** implementation defines canonical DTOs needed by strategy/config/data layers and later UI may reuse them
- **THEN** the work is allowed if no UI endpoints or dashboard surfaces are added

### Requirement: Monitoring, ops, and production hardening are deferred
The system SHALL specify monitoring, degraded mode, security, runbook, deployment, and production-hardening requirements now, but implementation of production healthchecks, alerting integrations, runbooks, deployment automation, immutable audit infrastructure, TLS/network policy, secret rotation automation, and SRE/ops workflows SHALL require later OpenSpec changes.

#### Scenario: Foundation code adds production ops integration
- **WHEN** implementation adds Slack/Telegram/email alerting, production health endpoints, deployment automation, secret rotation automation, or infrastructure policy enforcement during the foundation slice
- **THEN** the work is out of scope for the foundation slice

#### Scenario: Foundation code adds local validation errors
- **WHEN** implementation adds local validation errors for invalid config, degraded input data, or no-lookahead violations
- **THEN** the work is allowed as foundation correctness, not production ops hardening

### Requirement: Deferred-scope review checklist is mandatory
Before any deferred scope is implemented, its dedicated OpenSpec change SHALL identify source requirements, affected modules, non-goals, side-effect boundaries, test strategy, safety gates, rollback/cleanup plan where relevant, and explicit GO/NO-GO criteria.

#### Scenario: Deferred change lacks safety gates
- **WHEN** a deferred-scope change omits safety gates for credentials, broker side effects, production enablement, or operator actions where applicable
- **THEN** final review returns NO-GO until those gates are specified

### Requirement: First crypto experiments cannot access private trading scope
The first crypto historical experiment runner SHALL be read-only with respect to exchange and account state. It SHALL NOT submit, cancel, modify, query, or reconcile live orders or positions, and SHALL NOT require or read private API credentials or private account data.

#### Scenario: Private credentials are present or absent
- **WHEN** the first crypto historical experiment runner starts
- **THEN** it behaves the same whether private exchange API credentials are absent or present in the environment
- **AND** it does not read or print private API keys, secrets, authorization headers, account identifiers, balances, positions, or order history

#### Scenario: Live trading side effect is attempted
- **WHEN** implementation tries to add live order submission, cancellation, modification, position synchronization, account balance reads, private order-history reads, semi-auto confirmation, or full-auto execution to the first crypto experiment runner
- **THEN** the work is out of scope for this change
- **AND** implementation must stop until a separate reviewed OpenSpec change approves that scope

### Requirement: First crypto experiment conclusions remain research-only
The first BTCUSDT crypto historical experiment SHALL be represented as a reproducibility and research artifact only. It SHALL NOT claim production readiness, production OOS approval, live-trading readiness, or full-auto trading approval.

#### Scenario: Experiment report is reviewed
- **WHEN** a report artifact is generated by the first crypto historical experiment
- **THEN** the report or manifest makes clear that the run proves only data loading, normalization, deterministic backtesting, and artifact export
- **AND** FX support, multi-symbol crypto batch runs, optimization, walk-forward production approval, live execution, and production deployment remain separate follow-up scopes

### Requirement: Optional container execution remains local and non-production
If the first crypto historical experiment includes a container wrapper, the wrapper SHALL be limited to local reproducibility and isolation. It SHALL run the same public-data historical experiment as the host path and SHALL NOT introduce production deployment, registry publishing, cloud runtime, Kubernetes, VPS/systemd, or live service behavior.

#### Scenario: Containerized experiment is run locally
- **WHEN** the experiment is run through the optional container wrapper
- **THEN** it mounts only explicit input data paths and output artifact paths
- **AND** it does not mount `.env`, credential files, private keys, shell history, exchange credentials, or the whole home directory
- **AND** it produces deterministic artifacts equivalent to the host `uv run` path for the same fixture/public dataset

#### Scenario: Container scope expands toward deployment
- **WHEN** implementation attempts to publish images, configure registries, add cloud/VPS deployment automation, run long-lived services, or mount private credentials for the first crypto experiment
- **THEN** the work is out of scope for this change
- **AND** a separate reviewed OpenSpec change is required

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
