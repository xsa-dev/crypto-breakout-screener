# Proposal

## Why
The current BTCUSDT reference profile `conservative-v1-m15-slope-positive-max-trades-8` remains `5/8` over the required quarterly windows with failures in `2024q1`, `2024q2`, and `2024q4`. Prior entry filters, volatility regime filters, confirmation filters, fixed holding profiles, break-even profiles, trailing profiles, and the baseline-only tight ATR stop did not produce robust `8/8` after realistic costs. The tight `0.01 ATR` stop reached baseline `8/8` but was falsified by realistic costs because it was too turnover/cost-sensitive.

The next bounded path-risk/exit hypothesis is to test a small fixed set of asymmetric ATR stop/target exits that are less microscopic than `0.01 ATR`, keep downside controlled earlier than long fixed holds, and still allow larger favorable excursions. This targets the shared failed-window drawdown/path-risk mechanism without adding entry/no-trade filters or weakening thresholds.

If the asymmetric ATR candidates still fall short, this change may also evaluate a strictly bounded averaging/scale-in branch as research-only evidence. That branch is allowed only as a fixed, named profile with capped add count, capped total notional, unchanged thresholds, and full realistic-cost accounting on the added turnover. It is not allowed to become unbounded averaging, martingale sizing, or a way to hide failed drawdown.

## What Changes
Implement and evaluate exactly these named research-only exit profiles for the existing reference:

- `conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p25-target-2p0-hold-8`
- `conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p5-target-2p0-hold-8`
- `conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p75-target-2p5-hold-16`

Optionally, after the three asymmetric ATR candidates are measured, implement and evaluate a separate bounded averaging/scale-in research profile if the agent needs another hypothesis:

- `conservative-v1-m15-slope-positive-max-trades-8-bounded-scalein-1add-atr-stop-0p5-target-2p0-hold-8`

The implementation SHALL:

- preserve entry selection, lifecycle gates, M15 slope feature filter, max-trades risk control, regime filters, confirmation filters, and research thresholds unless the named exit profile is explicitly selected;
- keep bounded scale-in disabled unless the explicit named profile is selected;
- cap bounded scale-in at one additional entry, fixed add sizing, and fixed maximum total notional/exposure per trade;
- record bounded scale-in trigger, add count, effective average entry, added notional, and added turnover in JSON/CSV artifacts when that profile is selected;
- run the exact eight required windows `2023q1..2024q4`;
- record the pre-change scorecard from the archived reference and the post-change scorecard for each candidate;
- evaluate both baseline and realistic-cost results where success requires `8/8` after realistic costs (`commission_rate=0.00055` per side, stressed spread/slippage, and `funding_rate_per_bar > 0`);
- charge realistic costs on all original and additional entries/exits for bounded scale-in;
- archive the change as falsified evidence if no candidate reaches realistic-cost `8/8`.

## Success Criteria
- The new exit profile settings are disabled by default and do not change default/reference behavior.
- Each candidate is fixed, named, serialized in JSON/CSV summaries, and does not rely on broad parameter search.
- Quarterly scorecards include exactly `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, and `2024q4`.
- Configured thresholds remain unchanged: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, `require_no_feed_gaps=true`.
- Bounded scale-in is considered falsified if it improves gross or net profit but violates `min_max_drawdown=-0.35`, reduces the number of required quarters, or depends on unbounded add sizing.
- A success notification is sent only if a candidate reaches `8/8` after realistic costs.
- If the best candidate remains below `8/8`, tasks and artifacts record falsified/negative evidence, no success notification is sent, and the change is archived.

## Non-goals
- No live trading, production approval, broker/private API access, order book/стакан/DOM/L2/taker-flow, ML, broad optimization, push, MR, merge, or cloud delivery.
- No new entry filters, volatility filters, confirmation filters, or production risk changes beyond the explicit bounded scale-in research profile described above.
- No weakening thresholds, removing quarters, or counting baseline-only `8/8` as robust success.
- No unbounded averaging, martingale recovery, hidden leverage increase, or post-hoc parameter search.
