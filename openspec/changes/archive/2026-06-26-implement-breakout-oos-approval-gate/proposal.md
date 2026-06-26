# implement-breakout-oos-approval-gate

## Why

The approved `breakout-backtesting-reporting` capability requires explicit numeric OOS/business-validity thresholds before any production `full_auto` approval. The current backtest report can export deterministic OOS metrics, but there is no local machine-readable gate that blocks production approval when thresholds are missing or not met.

## What Changes

- Add a narrow local approval-gate contract for comparing a completed `BacktestReport` against configured production OOS thresholds.
- Block production `full_auto` approval when thresholds are absent, when required metrics are unavailable, or when report metrics fail configured thresholds.
- Keep the change broker-neutral and local-only: no live execution, no production enablement, no UI, no cloud delivery, and no credentialed integrations.

## Non-Goals

- No live broker/exchange/terminal adapter.
- No production `full_auto` enablement.
- No optimizer, walk-forward expansion, UI/operator dashboard, persistence migration, or deployment automation.
- No new capability spec; this change updates the existing `breakout-backtesting-reporting` capability.
