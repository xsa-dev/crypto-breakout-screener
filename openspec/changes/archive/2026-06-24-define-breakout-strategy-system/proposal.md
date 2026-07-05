## Why

The supplied `docs/ai/task/deep-research-report.md`, `docs/ai/task/Торговля пробоев.pdf`, and `docs/ai/task/IMG_2656.JPEG` define a breakout trading system that is much broader than the previous Bybit pump-retrace robot. The project needs OpenSpec requirements that capture the full breakout methodology before source implementation begins.

## What Changes

- Remove the obsolete `align-tradebot-to-reference-tz` change from the active OpenSpec backlog.
- Define a modular breakout trading system covering market data ingestion, normalization, level detection, setup scoring, scenario selection, entry modes, state machine, risk management, execution, persistence, audit trails, backtesting, reporting, operations, and documentation.
- Specify the discretionary-method rules from the infographic/PDF as testable system behavior: slow approach, consolidation/protorgovka, cascade levels, local extremum breakouts, trendline/naklonnaya breakouts, density support, retest, false breakout, add-ons, and 30/50/20 partial exits.
- Keep this as a specification/change-definition step only. No source implementation is included until the specs are reviewed and approved.

## Non-Goals

- No source code changes in this change-definition step.
- No live trading, live broker connection, or credentialed smoke tests while writing specs.
- No forced choice of a single broker/API implementation; the specs define provider abstractions and acceptance behavior.
- No promise that the current template can implement the entire system in one short iteration; tasks split the work into staged implementation slices.

## Capabilities

### New Capabilities
- `breakout-runtime-and-data`: Operating modes, market/data scope, no-lookahead rules, market data providers, and normalized event contracts.
- `breakout-level-engine`: Detection and validation of pivot, round-number, daily high/low, cascade, and trendline levels.
- `breakout-setup-scoring`: Setup evaluation, feature calculation, breakout score, scenario prioritization, and direction/context filters.
- `breakout-entry-state-machine`: Three entry modes, breakout confirmation, retest handling, false breakout handling, and the required finite state machine.
- `breakout-risk-position-execution`: Blocking risk manager, position sizing, add-ons, partial exits, stop movement, execution safety, and broker synchronization.
- `breakout-persistence-audit-config`: Versioned configuration, persistence entities, decision traces, auditability, and deterministic replay identifiers.
- `breakout-backtesting-reporting`: Backtest, paper trading, IS/OOS, walk-forward, Monte Carlo, metrics, reports, and acceptance gates.
- `breakout-operations-security-docs`: Monitoring, alerts, degraded modes, security baseline, runbooks, and documentation deliverables.
- `breakout-deferred-scope-gates`: Explicit NO-GO gates requiring separate OpenSpec changes for live broker execution, full-auto production, concrete live adapters, backtesting/reporting runtime, UI/operator dashboard, and monitoring/ops/production hardening.

### Modified Capabilities

None. Existing active OpenSpec capabilities are absent; the previous unrelated change was removed from active changes.

## Impact

- Affected future code areas: data ingestion/normalization, strategy engines, risk/execution modules, persistence schema, admin/config UI, reporting, tests, and docs.
- Affected future data model: bars, ticks, optional order book, levels, features, signals, orders, fills, positions, risk events, backtest runs, and config versions.
- Affected verification: unit tests, replay tests, backtests, walk-forward validation, Monte Carlo analysis, static checks, and no-live-trade safety gates.
- Source materials: `docs/ai/task/deep-research-report.md`, `docs/ai/task/Торговля пробоев.pdf`, and `docs/ai/task/IMG_2656.JPEG`.
- Deferred scope: live broker execution, production full-auto, concrete MT5/Bybit/live adapters, backtesting/reporting implementation, UI/operator dashboard, and monitoring/ops/production hardening are specification targets here but implementation NO-GO without later dedicated OpenSpec changes.
