# Proposal

## Why
The current BTCUSDT reference profile `conservative-v1-m15-slope-positive-max-trades-8` remains `5/8` over the required quarterly windows with failures in `2024q1`, `2024q2`, and `2024q4`. Prior entry filters, volatility regime filters, confirmation filters, and fixed hold/ATR target profiles did not produce a robust supported profile. A microscopic tight ATR stop reached baseline `8/8`, but realistic-cost robustness falsified it because turnover and edge per trade were too cost-sensitive.

The next bounded path-risk/exit hypothesis is to test break-even and trailing-style exits derived from the existing path-risk diagnostics: allow only already-accepted entries, wait for favorable ATR excursion, then protect or trail the trade while using a bounded maximum holding horizon. This directly targets failed-window adverse path risk without adding new entry/no-trade filters or weakening thresholds.

## What Changes
Implement and evaluate a small fixed set of named research-only exit profiles for the existing reference:

- `conservative-v1-m15-slope-positive-max-trades-8-breakeven-1p0-hold-8`
- `conservative-v1-m15-slope-positive-max-trades-8-trail-1p0-giveback-0p5-hold-8`
- `conservative-v1-m15-slope-positive-max-trades-8-trail-1p0-giveback-1p0-hold-16`

The implementation SHALL:

- preserve entry selection, lifecycle gates, M15 slope feature filter, max-trades risk control, confirmation filters, and research thresholds unless the named exit profile is explicitly selected;
- run or summarize the exact eight required windows `2023q1..2024q4`;
- record the pre-change scorecard from the archived reference and the post-change scorecard for each candidate;
- evaluate both baseline and realistic-cost results where success requires `8/8` after realistic costs (`commission_rate=0.00055` per side, stressed spread/slippage, and `funding_rate_per_bar > 0`);
- archive the change as falsified evidence if no candidate reaches realistic-cost `8/8`.

## Success Criteria
- The new exit profile settings are disabled by default and do not change default/reference behavior.
- Each candidate is fixed, named, serialized in JSON/CSV summaries, and does not rely on broad parameter search.
- Quarterly scorecards include exactly `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, and `2024q4`.
- Configured thresholds remain unchanged: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, `require_no_feed_gaps=true`.
- A success notification is sent only if a candidate reaches `8/8` after realistic costs.
- If the best candidate remains below `8/8`, tasks and artifacts record falsified/negative evidence, no success notification is sent, and the change is archived.

## Non-goals
- No live trading, production approval, broker/private API access, order book/стакан/DOM/L2/taker-flow, ML, broad optimization, push, MR, merge, or cloud delivery.
- No new entry filters, volatility filters, confirmation filters, or production risk changes.
- No weakening thresholds, removing quarters, or counting baseline-only `8/8` as robust success.
