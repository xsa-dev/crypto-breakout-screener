## Why

The current BTCUSDT breakout reference `conservative-v1-m15-slope-positive-max-trades-8` is still only `5/8` on the required quarterly scorecard (`2023q1..2024q4`) under the configured research thresholds. The archived reference scorecard fails `2024q1`, `2024q2`, and `2024q4`:

| Quarter | Reference status | Key blockers | Artifact |
| --- | --- | --- | --- |
| 2023q1 | pass | none | `artifacts/realistic-cost-profile-search/conservative-v1-m15-slope-positive-max-trades-8/scorecard.csv` |
| 2023q2 | pass | none | same |
| 2023q3 | pass | none | same |
| 2023q4 | pass | none | same |
| 2024q1 | fail | `net_profit_below_threshold`, `profit_factor_below_threshold`, `max_drawdown_below_threshold` | same |
| 2024q2 | fail | `net_profit_below_threshold`, `profit_factor_below_threshold`, `max_drawdown_below_threshold` | same |
| 2024q3 | pass | none | same |
| 2024q4 | fail | `max_drawdown_below_threshold` | same |

Archived entry filters, volatility filters, confirmation filters, simple extended holds, stops, trailing, partial exits, large targets, close-stop profiles, and realized drawdown guards did not move the research line to `8/8`. A likely shared mechanism remains: longer holding/exit hypotheses were evaluated while the backtest loop still allowed new trades during the synthetic holding interval, so holding profiles did not honestly model one active position occupancy and stayed cost/drawdown sensitive.

## What Changes

- Add a disabled-by-default research gate that blocks new entries while the previous simulated trade is still within its holding interval.
- Add a small fixed set of named occupancy-aware holding/target exit profiles derived from the existing `conservative-v1-m15-slope-positive-max-trades-8` profile.
- Evaluate these profiles through the real BTCUSDT quarterly `2023q1..2024q4` scorecard with unchanged thresholds.
- Record whether the best candidate reaches `8/8`; if it remains below `8/8`, archive the result as falsified/negative research evidence.

## Out of Scope

- No private/live API, live trading, broker execution, production approval, order book/DOM/L2/taker-flow, ML, or new market/data dimensions.
- No weakening of research thresholds, quarter coverage, or safety/deferred-scope gates.
- No broad parameter search; only fixed named profiles are allowed.

## Expected Outcome

The change proves or falsifies the hypothesis that one-position occupancy plus longer holding/target exits can reduce turnover/path risk enough to move the BTCUSDT quarterly scorecard toward `8/8` without changing entry filters or thresholds. Success requires all eight quarters to pass configured research thresholds; otherwise the artifacts must state the remaining failed quarters and blockers.
