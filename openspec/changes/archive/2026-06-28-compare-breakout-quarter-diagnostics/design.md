# Design

## Scope

This change is diagnostic-only. It creates the evidence layer that later algorithmic changes use to justify state, score, top-N selection, retest/confirmation, or fast-failure behavior.

## Diagnostic artifact

For each portfolio run, write `quarter-diagnostics.csv` and include its path in `summary.json`.

Each row SHALL contain:

- `window_label`, `status`, `blockers`;
- `candidate_count`, `accepted_trade_count`, `skipped_signal_count`;
- `net_profit`, `profit_factor`, `max_drawdown`;
- regime contribution fields for `bull_long`, `bear_short_or_avoid`, `neutral_blocked`;
- BTCUSDT/ETHUSDT context fields available at the window level;
- market breadth fields for the fixed universe;
- relative strength summary fields;
- optional ratios for cost-feasibility, confirmation/retest, and fast-failure features when those upstream artifacts exist.

## Comparison summary

Write `quarter-diagnostics-summary.json` with:

- lists of passing, failed, blocked, and unknown windows;
- strongest observed feature differences between passing and non-passing windows;
- fields unavailable in the current run;
- a warning when the diagnostic is underpowered because too few quarters have comparable statuses.

## Data rules

All diagnostics must be computed from public OHLCV/history and already-written run artifacts. The diagnostic may compare realized outcomes after a run, but it must label those values as outcome analysis and must not feed them into entry-time selection logic.
