## Context

The breakout source materials describe a full engineering product, not a small one-signal bot. The system must algorithmize a discretionary breakout methodology with levels, preparation, confirmation, retest, add-ons, false breakout handling, 30/50/20 exits, risk controls, backtesting, and operations. The current repository is a Python/uv educational crypto template, but these specs intentionally define the target behavior before deciding how much of it to implement in each iteration.

The key design constraint is reproducibility: every signal and trade decision must be explainable from market data, configuration, and account/risk state without look-ahead bias. Live/full-auto execution must be gated behind advisory/paper/semi-auto stages and a blocking risk manager.

## Goals / Non-Goals

**Goals:**

- Capture the full breakout strategy from the report, PDF, and infographic as OpenSpec requirements.
- Split the system into independently implementable capabilities.
- Define testable rules for data, levels, setup score, entry modes, state machine, risk, persistence, backtesting, operations, and documentation.
- Preserve safety: no live order side effects before explicit implementation approval and safe credentials/test environment.

**Non-Goals:**

- No source implementation in this spec-forming step.
- No broker-specific lock-in; broker/terminal adapters must satisfy abstract contracts.
- No hidden discretionary steps: if a rule affects trading, it must be represented in config, decision trace, or explicit manual override.

## Decisions

### Decision 1: Separate the breakout system from the previous pump-retrace bot

The previous `align-tradebot-to-reference-tz` change is removed because it targeted a Bybit pump-retrace robot, not the supplied breakout strategy. The new change defines a separate capability set.

Rationale: mixing both scopes would produce unreviewable specs and unsafe implementation boundaries.

### Decision 2: Use staged operation modes

The system SHALL support `advisory-only`, `semi-auto`, and `full-auto` modes. Full-auto execution is a mode, not the default acceptance path. Historical backtest, paper trading, and reduced-risk pilot stages must precede production use.

Rationale: the source report explicitly warns that discretionary breakout logic must be formally verified before live automation.

### Decision 3: Model strategy logic as engines plus a finite state machine

Level detection, feature/setup scoring, signal/scenario selection, risk, execution, and persistence remain separate modules. The trade lifecycle is governed by a finite state machine with required states and transition conditions.

Rationale: this makes decisions testable and prevents signal code from directly opening trades.

### Decision 4: No-lookahead is a hard invariant

Pivot, cascade, local-extremum, and confirmation rules must only use closed bars and confirmed patterns in online mode. Pivots requiring right-window bars become valid only after those bars close.

Rationale: without this invariant, backtest and live behavior diverge.

### Decision 5: Risk manager is blocking

Signal Engine emits `TradeIntent`; Risk Manager approves or rejects it with reason codes. Execution Engine cannot bypass risk approval.

Rationale: position sizing, add-ons, daily loss, and max-open-position limits are acceptance criteria, not advisory hints.

### Decision 6: Persistence stores enough to replay and audit

The system stores market data references, levels, features, signals, orders, fills, positions, risk events, backtest runs, config versions, and decision traces. Each decision references dataset/config hashes where applicable.

Rationale: the source materials require reproducibility, audit, and reporting.

### Decision 7: First implementation GO is foundation-only

The first implementation GO after this spec review SHALL be limited to the foundation slice: config models, canonical data models, market data provider interfaces, normalization, level engine, setup scoring, and no-lookahead tests. Broker execution, full-auto operation, backtesting/reporting, UI/operator surfaces, monitoring/ops, production security hardening, and live adapters are deferred to later OpenSpec-reviewed slices.

Rationale: the full breakout product is too broad for one safe implementation pass. A foundation-only first slice proves the market-data and strategy-decision core before any broker side effects or UI/runtime expansion.

### Decision 8: First implementation slice has no live broker execution

The first implementation slice SHALL NOT submit live orders or choose a concrete live broker adapter. It may define execution interfaces and fake/test adapters only when needed to validate contracts; MT5, Bybit, or any other live adapter requires a later approved change.

Rationale: execution semantics and credentials are high-risk and should follow verified level/scoring/state foundations.

## Risks / Trade-offs

- [Risk] Full scope is large for one implementation pass. → Mitigation: first GO is explicitly foundation-only; execution/full-auto/backtesting/UI/ops are deferred slices.
- [Risk] DOM/density data may be unavailable for some markets. → Mitigation: order book is optional; density score must record unavailable/neutral behavior and may use configured proxies.
- [Risk] Broker APIs differ in order semantics. → Mitigation: use provider/execution abstractions and adapter-specific verification.
- [Risk] Strategy overfitting during optimization. → Mitigation: require IS/OOS split, walk-forward, Monte Carlo, stability analysis, and config/dataset hashes.
- [Risk] Live trading safety. → Mitigation: require advisory/paper/reduced-risk stages, risk gates, degraded mode, reconnect safety, and no live order verification without explicit safe setup.

## Migration Plan

1. Review and approve these OpenSpec artifacts.
2. Implement only the foundation slice: config models, canonical data models, provider interfaces, normalization, level engine, setup scoring, and no-lookahead tests.
3. Verify the foundation slice with unit/replay tests and no live trading side effects.
4. Add later OpenSpec-reviewed slices for entry/FSM/risk, execution/live adapters, backtesting/reporting, UI/operator surfaces, monitoring/ops, and production hardening.

## Open Questions

None for the spec baseline. Broker-specific adapter choices are explicitly deferred beyond the first foundation implementation slice.
