# Proposal

## Why

The archived `evaluate-breakout-altcoin-universe-profiles` shared-bankroll portfolio slice falsified the first fixed-50 altcoin portfolio smoke. Its strongest evaluated portfolio profile, `conservative-v1-m15-slope-positive-max-trades-8-target-4p0-hold-32`, failed the blocker quarter `2024q1` before promotion:

- baseline scorecard before this change: `2024q1=blocked`, `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q2`, `2024q3`, `2024q4=unknown/not promoted`;
- artifact: `artifacts/altcoin-universe-portfolio-comparison-regime-smoke-reaggregated-ledger-fix/conservative-v1-m15-slope-positive-max-trades-8-target-4p0-hold-32/520b158e637db140/summary.json`;
- `2024q1` blockers: `portfolio_symbol_blockers_present`, `net_profit_below_threshold`, `profit_factor_below_threshold`, `max_drawdown_below_threshold`;
- key metrics: net profit `-9799.606491774299`, profit factor `0.1283106575002619`, max drawdown `-0.979960649177431`, accepted trades `788`, skipped/blocked regime/exposure signals `1564`, blocked symbols `43`;
- per-regime evidence: `bull_long` accepted trades alone contributed `-9799.606491774299` PnL and `-0.9799606491774299` drawdown, while `bear_short_or_avoid` and `neutral_blocked` were risk-off skipped.

The failure mechanism includes unrealistic acceptance of entries whose price/cost geometry is structurally dominated by configured absolute spread/slippage costs. Before richer algorithmic work can be trusted, the shared-bankroll runner needs a deterministic cost-feasibility gate that skips such candidates without weakening costs, thresholds, quarter coverage, or the fixed approved universe.

This is a foundation change only. It does not claim to implement the full breakout concept. Follow-up OpenSpec changes cover lifecycle/state audit, quarter diagnostics, algorithmic scoring, top-N portfolio selection, retest/confirmation behavior, and fast-failure exits.

## What Changes

Implement one opt-in shared-bankroll portfolio selection profile:

`cost-feasible-v1`

The profile SHALL:

- preserve the approved fixed-50 altcoin universe and evaluate all symbols for promoted portfolio runs;
- keep starting equity `10000 USDT`, realistic costs, per-trade notional cap, total open-exposure cap, no implicit leverage, and configured research thresholds unchanged;
- reject unsupported/private symbols and missing public history exactly as before;
- skip, not delete, long entries whose entry-time price/cost geometry is not cost-feasible under the configured spread/slippage/commission/funding settings;
- record skipped signal counts and PnL/drawdown contribution by regime and by portfolio selection reason;
- keep per-symbol contribution and one combined portfolio equity curve as the success unit;
- allow smoke on `2024q1`, then require full promoted scorecard `2023q1..2024q4` only if the smoke result is technically valid and materially closer to the configured thresholds.

## Success Criteria

- The portfolio CLI and programmatic runner accept `--selection-profile cost-feasible-v1` while default behavior remains unchanged.
- The portfolio trade ledger records `portfolio_selection_cost_feasibility` blockers for skipped long entries and keeps them in skipped/blocked counts.
- Portfolio summary artifacts include the active selection profile, selection settings, and per-window selection skip counts.
- Per-regime reports include skipped/blocked signals caused by the selection gate and still expose `bull_long`, `bear_short_or_avoid`, and `neutral_blocked` contribution.
- `2024q1` smoke is rerun for the fixed-50 universe with realistic costs. The scorecard must state status, blockers, net profit, profit factor, max drawdown, exposure/skipped trades, feed-gap or technical blockers, and artifact path before deciding whether to promote.
- If promoted, the portfolio scorecard must use all eight quarters `2023q1..2024q4`, one shared `10000 USDT` bankroll, realistic net-of-cost accounting, configured thresholds, no missing feed gaps for the promoted universe run, and full per-regime reporting.
- `8/8` success notification is allowed only if the promoted shared-bankroll portfolio scorecard passes every required quarter with complete regime reporting.
- If the promoted run is completed and remains below `8/8`, archive this change as falsified/negative evidence with scorecards and artifacts. If smoke is technically blocked by unavailable public data, record the exact blocker instead of substituting another universe or lowering criteria.

## Non-goals

- No threshold weakening, no reduced quarter coverage, no reduced approved universe for promoted success evidence, no proxy per-symbol pass/fail success, no live/private API, no production approval, no short-side implementation, no ML, no order book/DOM/L2/taker-flow, no lifecycle state machine, no algorithmic score, no top-N ranking, no retest/confirmation implementation, no fast-failure exit, no broad parameter search, no push/MR/merge/cloud delivery.
