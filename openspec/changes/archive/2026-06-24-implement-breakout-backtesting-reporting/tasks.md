## 1. Backtest engine

- [x] 1.1 Review existing strategy/foundation/risk/persistence contracts.
- [x] 1.2 Implement deterministic backtest runner using the same closed-bar information boundary as online evaluation.
- [x] 1.3 Implement configurable spread, commission, slippage, and funding/swap assumptions.
- [x] 1.4 Implement paper-trading run mode or deterministic fake-live replay where useful.

## 2. Analysis and reports

- [x] 2.1 Implement IS/OOS, walk-forward, Monte Carlo, and stability analysis primitives or scoped local equivalents.
- [x] 2.2 Implement metrics and report artifacts for equity, drawdown, returns, trades, scenarios, scores, false breakouts, slippage, and parameter snapshots.
- [x] 2.3 Implement CSV export and Parquet export if dependencies are already present or can be added through `uv`.

## 3. Verification

- [x] 3.1 Add deterministic replay tests, no-lookahead backtest tests, and report shape/export tests.
- [x] 3.2 Run `uv run ruff check .`.
- [x] 3.3 Run `uv run pyright` or document the local blocker if pyright is unavailable.
- [x] 3.4 Run `uv run pytest`.
- [x] 3.5 Run OpenSpec validation for this change and all specs.
