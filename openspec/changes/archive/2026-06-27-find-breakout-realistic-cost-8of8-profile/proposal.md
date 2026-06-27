# Proposal

## Why
The archived tight ATR exit profile reached `8/8` quarterly BTCUSDT score under legacy costs, but the follow-up realistic-cost stress falsified that robustness: notional commission alone turned the ledger-level result into `0/8`. The research goal therefore remains open: find a BTCUSDT breakout profile that passes every required quarter after realistic costs, not merely under legacy or baseline assumptions.

The next slice should move away from microscopic tight-stop / one-bar / high-turnover profiles. The search must prefer lower turnover, larger average trade, and sufficient gross edge per trade so explicit round-trip costs do not consume the edge.

## What Changes
Create a research-only OpenSpec change to search for a robust BTCUSDT breakout profile that:

- evaluates exactly the eight required quarterly windows: `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, `2024q4`;
- preserves the current thresholds: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, `require_no_feed_gaps=true`;
- checks baseline/legacy evidence only as a pre-screen, not as success;
- requires realistic costs before any success verdict: `commission_rate=0.00055` per side, stressed spread/slippage, and `funding_rate_per_bar > 0` for conservative stress;
- records every candidate with `summary.json`, `scorecard.csv`, serialized `cost_model_settings`, per-quarter pass/fail status, and blockers;
- archives baseline-only `8/8` profiles that fail realistic costs as falsified robustness evidence and continues to the next hypothesis;
- sends Telegram success notification only for `8/8` after realistic costs.

## Success Criteria
- The implementation compares fixed, named candidate profile(s) that deliberately reduce turnover versus the falsified tight ATR profile using cooldown, max trades, regime filters, exit horizon, or similar bounded controls.
- Every candidate run records baseline and realistic-cost verdicts separately.
- The required eight-quarter set is not reduced and no threshold is weakened.
- A profile is successful only when all eight quarters pass after the required realistic-cost settings.
- Baseline-only `8/8` is explicitly marked insufficient and, when it fails realistic costs, archived as falsified robustness evidence.
- No Telegram success notification is sent for baseline-only `8/8`.
- Telegram success notification is sent or send failure recorded only when a profile reaches `8/8` after realistic costs.

## Non-goals
- No live trading, production approval, broker API, balances, orders, positions, private exchange data, `.env` access, push, MR, merge, or cloud delivery.
- No weakening thresholds and no reducing the quarterly window set.
- No broad unconstrained parameter search, no ML, and no order book / стакан / DOM / L2 / taker-flow data dimension in this slice.
- No production fee guarantee; realistic costs are explicit conservative local research assumptions.
