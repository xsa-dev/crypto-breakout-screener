# Proposal

## Why
The forward-path / MAE / MFE diagnostics for `conservative-v1-m15-slope-positive-max-trades-8` showed that simply adding more entry filters is not the right next step, and simple longer holding is not clearly justified either:

- positive-forward-return ratios stayed near 46%-50%;
- median forward returns were often near zero or negative;
- failed windows were not cleanly worse than passed windows by forward return or MFE;
- nearly all measured trades crossed below entry within the diagnostic horizons;
- failed windows showed larger favorable excursion and larger adverse excursion, suggesting path risk rather than a simple absence of movement.

Before implementing any exit, stop, trailing, break-even, or holding rule, the next step should diagnose path ordering and path-risk feasibility: whether trades tend to hit favorable thresholds before adverse thresholds, what adverse excursion must be tolerated before continuation, and whether any exit idea has evidence without changing the strategy yet.

## What changes
Add diagnostic-only path-risk and exit-feasibility artifacts for the current best BTCUSDT profile:

- threshold-hit ordering diagnostics for fixed favorable/adverse ATR multiples;
- MFE-before-MAE ordering summaries;
- stop-distance feasibility tables;
- break-even/trailing feasibility labels;
- passed-vs-failed path-risk comparison summaries.

This change must not implement new exits. It only labels the already-produced trades with offline path-risk diagnostics.

## Non-goals
- No new entry filters, no-trade filters, confirmation filters, or regime filters.
- No actual stop-loss, take-profit, trailing-stop, break-even, holding, or position-management rule changes.
- No changes to actual realized backtest metrics or batch verdict logic.
- No production/live trading behavior.
- No private exchange API, balances, orders, positions, `.env`, authorization headers, or private endpoints.
- No order book, стакан, DOM, L2 depth, footprint, taker-flow, or trade tape data.
- No ML, boosting, neural networks, LLM trading decisions, or automatic threshold optimization.
- No new market, symbol, or timeframe scope.

## Success criteria
- Path-risk diagnostics are deterministic and no-lookahead-safe as offline labels.
- Enabling diagnostics does not alter trade selection, realized metrics, or verdicts.
- Quarterly 2023-2024 BTCUSDT diagnostics run for the current best profile.
- The result answers whether a future OpenSpec for stop/exit/holding profiles is justified, and which path-risk hypothesis to test first.
- OpenSpec validation, tests, lint, type checks, and git diff hygiene pass.
