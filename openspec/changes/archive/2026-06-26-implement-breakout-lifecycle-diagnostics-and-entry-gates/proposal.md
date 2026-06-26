# implement-breakout-lifecycle-diagnostics-and-entry-gates

## Why
The BTCUSDT quarterly batch research run showed technically valid data/backtest execution but rejected the trading hypothesis across all windows. Investigation found the immediate cause of excessive trade count and drawdown: the current deterministic backtest opens long trades on almost every M15 bar, closes every trade on the next bar, and commonly re-enters at the previous exit timestamp. This makes the experiment behave like a one-bar always-long scalper rather than a lifecycle-aware breakout simulation.

Before expanding to ETH/top-N, optimizing parameters, or adding HTF strategy logic, the system needs reproducible lifecycle diagnostics and conservative research entry gates that let us quantify and control overtrading.

## What
- Add deterministic lifecycle diagnostic exports to completed backtest reports:
  - trade grouping by day and week;
  - trade frequency per day/week;
  - daily and weekly net PnL;
  - holding-period distribution;
  - consecutive re-entry diagnostics;
  - losing-streak diagnostics;
  - score-bucket PnL diagnostics;
  - side distribution;
  - entry/level metadata sufficient to see repeated same-level/regime trading when available.
- Add configurable research-only entry gates to the local backtest configuration/path:
  - minimum score threshold override;
  - cooldown bars after any trade;
  - cooldown bars after losing trade;
  - block immediate re-entry at the previous exit timestamp;
  - max trades per UTC day;
  - optional daily stop-loss gate.
- Ensure gates are explicit, deterministic, and recorded in report parameter snapshots and batch summaries.
- Repeat the BTCUSDT quarterly batch with at least baseline and one conservative gated profile so the user can compare trade count, drawdown, PnL, and verdict.

## Out of scope
- Live trading, broker adapters, order placement, balances, positions, or private API access.
- ETH/top-N expansion.
- Parameter optimization/search frameworks.
- Production OOS/full-auto approval.
- UI/dashboard.
- Concrete HTF strategy logic that consumes H1/H4/D1 as trading filters. HTF filter design remains a separate follow-up unless this diagnostic pass proves simple lifecycle gates are insufficient.
- Rewriting the entire backtest engine into a full position simulator with partial exits/add-ons/trailing stops. This change may expose the limitation and add gates, but does not claim full production lifecycle fidelity.

## Acceptance criteria
- Reports include deterministic day/week and lifecycle diagnostics for the current backtest artifacts.
- Diagnostics prove whether excessive trade count comes from one-bar holding and immediate re-entry.
- Research entry gates can reduce trade frequency deterministically without changing downloader/data contracts.
- Batch summaries include enough fields to compare baseline vs gated profiles.
- The first repeated BTCUSDT quarterly batch produces a visible before/after table and a research-only verdict.
- All tests, Ruff, Pyright, OpenSpec validation, and `git diff --check` pass.
