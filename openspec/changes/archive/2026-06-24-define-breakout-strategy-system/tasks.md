## 1. Source-material and spec review

- [ ] 1.1 Confirm that `deep-research-report.md`, `Торговля пробоев.pdf`, and `IMG_2656.JPEG` are the authoritative source materials for the breakout strategy.
- [ ] 1.2 Review all nine capability specs for semantic coverage of the source materials and deferred-scope gates.
- [ ] 1.3 Confirm first implementation GO is foundation-only: config models, canonical data models, market data provider interfaces, normalization, level engine, setup scoring, and no-lookahead tests.
- [ ] 1.4 Confirm deferred scope for later OpenSpec-reviewed slices: broker execution, full-auto operation, backtesting/reporting, UI/operator surfaces, monitoring/ops, production security hardening, and live adapters.
- [ ] 1.5 Confirm `breakout-deferred-scope-gates` blocks each deferred scope unless a later dedicated OpenSpec change approves it.

## 2. Runtime/data foundation implementation slice

- [ ] 2.1 Define config models for operation modes, symbols, timeframes, data sources, and baseline parameters.
- [ ] 2.2 Implement market data provider abstractions for bars, ticks, and optional order book snapshots.
- [ ] 2.3 Implement normalization: UTC timestamps, deduplication, resampling/gap handling, and canonical OHLCV/tick shapes.
- [ ] 2.4 Add no-lookahead tests for closed-bar-only and pivot right-window behavior.

## 3. Level/setup/signal implementation slice

- [ ] 3.1 Implement pivot high/low, round-number, daily high/low, cascade, and trendline level detection.
- [ ] 3.2 Implement level validity: min touches, H1/M15 visibility, reaction threshold, and recent-break invalidation.
- [ ] 3.3 Implement features: ATR, EMA50/EMA200, ADX, consolidation, slow approach, activity, and density/proxy.
- [ ] 3.4 Implement breakout score weights, 70/50 thresholds, and scenario priority order.
- [ ] 3.5 Add unit and replay tests for all level/setup/scenario rules.

## 4. Entry/state-machine/risk/execution implementation slice

- [ ] 4.1 Implement the required finite state machine and transition logging.
- [ ] 4.2 Implement pre-entry, at-level, and post-breakout entry intents with 30/30/40 default shares.
- [ ] 4.3 Implement breakout confirmation, retest validation, false breakout handling, add-ons, and 30/50/20 partial exits.
- [ ] 4.4 Implement blocking Risk Manager with position sizing, add-on risk budget, daily loss, and max-open-position limits.
- [ ] 4.5 Implement execution adapters only after selecting broker/API scope; verify with fake adapters before live credentials.
- [ ] 4.6 Keep live broker execution out of the foundation slice; only interfaces/fakes are allowed before a later approved execution change.

## 5. Persistence/audit/config implementation slice

- [ ] 5.1 Implement persistence entities for bars, ticks, order book, levels, features, signals, orders, fills, positions, risk events, backtest runs, and config versions.
- [ ] 5.2 Implement decision traces linking levels, features, score factors, risk decisions, orders, fills, and manual overrides.
- [ ] 5.3 Implement config version hashing and dataset hashing for deterministic replay.

## 6. Backtesting/reporting implementation slice

- [ ] 6.1 Implement deterministic backtest runs with spread, commission, slippage, and funding/swap where applicable.
- [ ] 6.2 Implement IS/OOS, walk-forward, Monte Carlo, and stability analysis.
- [ ] 6.3 Implement reports: equity curve, drawdown, return distribution, trade list, scenario breakdown, score distribution, false breakout analysis, slippage report, parameter snapshot, and CSV/Parquet export.

## 7. Operations/security/docs implementation slice

- [ ] 7.1 Implement healthchecks, degraded mode, reconnect/order idempotency checks, and risk-stop alerts.
- [ ] 7.2 Implement security baseline: secrets outside source, least privilege, rotation guidance, role separation, TLS guidance, immutable audit trail requirements.
- [ ] 7.3 Produce user guide, operator guide, API spec, configuration manual, test methodology, test report, deployment guide, runbook, changelog/config changelog, and QA checklists.

## 8. Verification gates

- [ ] 8.1 Run OpenSpec validation for this change and all specs.
- [ ] 8.2 Run project static checks and tests for each implementation slice once source changes exist.
- [ ] 8.3 Record skipped live trading verification unless explicit safe credentials/testnet configuration is provided.
- [ ] 8.4 Final acceptance requires deterministic replay, no-lookahead proof, risk-limit tests, reconnect/idempotency tests, and backtest/report artifacts.

## 9. Deferred-scope gate checks

- [ ] 9.1 Verify live broker execution remains NO-GO without a dedicated execution change.
- [ ] 9.2 Verify production `full_auto` remains NO-GO without a dedicated full-auto approval change.
- [ ] 9.3 Verify concrete MT5, Bybit, exchange, broker, or terminal adapters remain NO-GO without dedicated adapter changes.
- [ ] 9.4 Verify backtesting/reporting runtime remains NO-GO without a dedicated backtesting/reporting change.
- [ ] 9.5 Verify UI/operator dashboard implementation remains NO-GO without a dedicated UI/operator change.
- [ ] 9.6 Verify monitoring/ops/production hardening remains NO-GO without dedicated ops/security changes.

## 10. Final review checklist before implementation GO

- [ ] 10.1 Run `npx --yes @fission-ai/openspec@1.4.1 validate define-breakout-strategy-system --strict --no-interactive`.
- [ ] 10.2 Run `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`.
- [ ] 10.3 Review `source-traceability.md` and confirm all source materials are mapped to specs.
- [ ] 10.4 Confirm no `src/` implementation code was touched during spec formation.
- [ ] 10.5 Confirm first slice is foundation-only and live trading is explicitly out of scope.
- [ ] 10.6 List implementation blockers or deferred decisions, including broker/live adapter choice and production OOS thresholds.
