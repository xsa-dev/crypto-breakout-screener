# Source Traceability Matrix

This matrix maps the supplied breakout source materials to OpenSpec capabilities. It is a review aid; normative requirements live in `specs/*/spec.md`.

## Source files

- `docs/ai/task/deep-research-report.md`
- `docs/ai/task/Торговля пробоев.pdf`
- `docs/ai/task/IMG_2656.JPEG`

## Deep research report → specs

| Source section / requirement | Covered by spec capability |
|---|---|
| Operating stages: historical analysis, paper trading, reduced-risk pilot, production | `breakout-runtime-and-data`, `breakout-backtesting-reporting`, `breakout-operations-security-docs` |
| Modes: advisory-only, semi-auto, full-auto | `breakout-runtime-and-data`, `breakout-persistence-audit-config` |
| Markets: forex, crypto, futures, CFD, stocks | `breakout-runtime-and-data` |
| Timeframes M15, H1, H4, D1 | `breakout-runtime-and-data`, `breakout-persistence-audit-config` |
| OHLCV bars, ticks, optional DOM/order book | `breakout-runtime-and-data`, `breakout-persistence-audit-config` |
| UTC normalization, deduplication, feed gaps | `breakout-runtime-and-data`, `breakout-operations-security-docs` |
| No-lookahead and pivot right-window confirmation | `breakout-runtime-and-data`, `breakout-level-engine` |
| Pivot High / Pivot Low | `breakout-level-engine` |
| Round Number levels | `breakout-level-engine` |
| Daily High / Daily Low levels | `breakout-level-engine` |
| Cascade levels | `breakout-level-engine`, `breakout-setup-scoring`, `breakout-risk-position-execution` |
| Trendline / Naklonnaya | `breakout-level-engine`, `breakout-setup-scoring` |
| Level validity: min touches, reaction, visibility, recent break | `breakout-level-engine` |
| SetupEvaluator factors: consolidation, slow approach, trend, activity, density | `breakout-setup-scoring` |
| EMA50/EMA200, ADX, ATR factors | `breakout-setup-scoring`, `breakout-persistence-audit-config` |
| Breakout score, thresholds 70/50/<50 | `breakout-setup-scoring`, `breakout-persistence-audit-config` |
| Three entry modes: pre-entry, at-level, post-breakout | `breakout-entry-state-machine`, `breakout-persistence-audit-config` |
| Breakout confirmation formula | `breakout-entry-state-machine` |
| Retest validity and micro-impulse | `breakout-entry-state-machine`, `breakout-risk-position-execution` |
| False breakout and optional reversal | `breakout-entry-state-machine`, `breakout-persistence-audit-config` |
| Add-ons and average-price degradation | `breakout-risk-position-execution` |
| 30/50/20 partial exit framework | `breakout-risk-position-execution`, `breakout-persistence-audit-config` |
| Fast exit for low breakouts | `breakout-risk-position-execution` |
| Required finite state machine | `breakout-entry-state-machine`, `breakout-persistence-audit-config` |
| TradeIntent and blocking Risk Manager | `breakout-risk-position-execution`, `breakout-persistence-audit-config` |
| Position sizing and remaining risk budget | `breakout-risk-position-execution` |
| Architecture modules: ingestion, normalizer, level, feature, signal, risk, execution, persistence, reporting, UI, monitoring | All capability specs, especially `breakout-runtime-and-data`, `breakout-risk-position-execution`, `breakout-persistence-audit-config`, `breakout-backtesting-reporting`, `breakout-operations-security-docs` |
| Persistence entities: bars, ticks, order_book, levels, features, signals, orders, fills, positions, risk_events, backtest_runs, config_versions | `breakout-persistence-audit-config` |
| Backtesting: IS/OOS, walk-forward, Monte Carlo, costs, metrics | `breakout-backtesting-reporting` |
| Reports: equity, drawdown, returns, trade list, scenario breakdown, score distribution, false breakout analysis, slippage, parameter snapshot, CSV/Parquet | `breakout-backtesting-reporting` |
| Documentation: user/operator/API/config/test/deploy/runbook/QA | `breakout-operations-security-docs` |
| Security: secrets, least privilege, rotation, role separation, audit logs, TLS | `breakout-operations-security-docs` |
| Deferred implementation boundaries for live execution, full-auto, adapters, backtesting/reporting, UI, and ops | `breakout-deferred-scope-gates` |

## PDF / infographic blocks → specs

| PDF / IMG block | Covered by spec capability |
|---|---|
| “Вход заранее” | `breakout-entry-state-machine`, `breakout-risk-position-execution` |
| “Вход в пробой верхней границы проторговки” | `breakout-entry-state-machine`, `breakout-setup-scoring` |
| “Вход от нижней границы проторговки” | `breakout-entry-state-machine` |
| “Пробой каскадных уровней” | `breakout-level-engine`, `breakout-setup-scoring`, `breakout-risk-position-execution` |
| “Пробой локального максимума” | `breakout-level-engine`, `breakout-setup-scoring`, `breakout-entry-state-machine` |
| “Плотность в сторону пробоя” | `breakout-setup-scoring`, `breakout-risk-position-execution` |
| “Плотность как стоп-лосс / выход при разъедании” | `breakout-risk-position-execution` |
| “Добавляемся при пробое хая / локальных уровней” | `breakout-risk-position-execution` |
| “Скидываем добавленную часть при вкате до уровня добавления” | `breakout-risk-position-execution` |
| “Закрытие позиции: 3/10, 5/10, 2/10” | `breakout-risk-position-execution` |
| “Стоп-лосс переносим в безубыток” | `breakout-risk-position-execution` |
| “Основная стратегия пробоев с ретестом” | `breakout-entry-state-machine`, `breakout-risk-position-execution` |
| “State Machine / конечный автомат” | `breakout-entry-state-machine`, `breakout-persistence-audit-config` |
| “Выбор сценария пробоя” | `breakout-setup-scoring`, `breakout-entry-state-machine` |
| “Оценка качества пробоя / Breakout Score” | `breakout-setup-scoring` |
| “Risk Manager / управление риском” | `breakout-risk-position-execution` |
| “Направление рынка и поводыри” | `breakout-setup-scoring` |

## Review notes

- First implementation GO is foundation-only: config models, canonical data models, provider interfaces, normalization, level engine, setup scoring, and no-lookahead tests.
- Execution/full-auto/backtesting/UI/ops are mapped here but deferred to later OpenSpec-reviewed implementation slices.
- `breakout-deferred-scope-gates` is the normative NO-GO capability for these deferred scopes.
