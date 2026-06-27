# Proposal

## Why

The current BTCUSDT reference profile `conservative-v1-m15-slope-positive-max-trades-8` is still `5/8` over the required quarterly windows `2023q1..2024q4`. The failing quarters are `2024q1`, `2024q2`, and `2024q4`; configured research thresholds remain unchanged: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, and `require_no_feed_gaps=true`.

Archived path-risk/exit work has falsified immediate intrabar ATR stops, immediate close stops, break-even/trailing exits, fixed holds, target-only exits, large-target close stops, partial/protected residual exits, occupancy-aware holds, realized drawdown guards, and exposure scaling under realistic costs. The recurring blocker is that immediate adverse protection adds churn or still fails drawdown, while large-target/fixed-hold variants can create enough gross edge in some failed windows but tolerate too much sustained adverse path.

This change tests one distinct path-risk mechanism: a delayed close-stop that activates only after a short grace period. It is meant to tolerate noisy early adverse excursion before continuation, then clip sustained post-entry failures using close-only information. The primary target mechanism is `2024q1`/`2024q2` drawdown and negative expectancy without repeating immediate close-stop or intrabar-stop methods.

## What Changes

- Add disabled-by-default fixed exit-profile fields for delayed close-stop activation.
- Add fixed named profiles that combine delayed close stops with already-supported holding/target behavior:
  - `conservative-v1-m15-slope-positive-max-trades-8-delayed-close-stop-1p0-after-4-hold-16`
  - `conservative-v1-m15-slope-positive-max-trades-8-target-3p0-delayed-close-stop-1p0-after-4-hold-32`
  - `conservative-v1-m15-slope-positive-max-trades-8-close-target-2p0-delayed-close-stop-1p0-after-4-hold-32`
- Preserve entry scoring, M15 slope filter, max-trades risk control, confirmation/regime filters, cost assumptions, scorecard windows, and thresholds.
- Run realistic-cost BTCUSDT quarterly evidence. A candidate may be early-falsified after a required quarter fails, but missing quarters must be visible as blocked/not run and cannot count as passes.

## Scope Boundaries

- No private/live API, no account data, no order placement, no production approval.
- No lowered thresholds, removed quarters, fixture-only success, or proxy metrics.
- No broad parameter optimization, ML, order book/DOM/L2/taker-flow, or new data dimensions.
- No new entry/no-trade filters; this is an exit/holding path-risk profile comparison only.

## Reference scorecard before implementation

Command/artifact used for the archived reference: `artifacts/realistic-cost-profile-search/conservative-v1-m15-slope-positive-max-trades-8/scorecard.csv`.

| Quarter | Status | Net profit | Profit factor | Max drawdown | Blockers |
| --- | --- | ---: | ---: | ---: | --- |
| 2023q1 | pass | 5614.00 | 1.1364 | -0.3157 | none |
| 2023q2 | pass | 7018.80 | 1.1949 | -0.3471 | none |
| 2023q3 | pass | 4324.80 | 1.1820 | -0.1866 | none |
| 2023q4 | pass | 7203.20 | 1.1232 | -0.2635 | none |
| 2024q1 | fail | -6187.60 | 0.9542 | -1.1749 | net_profit_below_threshold; profit_factor_below_threshold; max_drawdown_below_threshold |
| 2024q2 | fail | -483.60 | 0.9957 | -0.7581 | net_profit_below_threshold; profit_factor_below_threshold; max_drawdown_below_threshold |
| 2024q3 | pass | 28130.00 | 1.2489 | -0.2225 | none |
| 2024q4 | fail | 9230.40 | 1.0551 | -0.4225 | max_drawdown_below_threshold |

Reference score: `5/8`; failing quarters: `2024q1`, `2024q2`, `2024q4`; `hypothesis_supported=false`.

## Success / falsification

Success requires realistic-cost `8/8` over exactly `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, and `2024q4` with unchanged thresholds and complete artifacts. If all fixed delayed close-stop candidates are evaluated or early-falsified below `8/8`, the change is archived as falsified negative evidence and no success notification is sent.

## Final research evidence

- Summary artifact: `artifacts/delayed-close-stop-exit-profile-comparison/early-falsified/summary.json`
- Scorecard artifact: `artifacts/delayed-close-stop-exit-profile-comparison/early-falsified/scorecard.csv`
- Realistic-cost settings: `spread=1.0`, `slippage_per_unit=0.5`, `commission_per_unit=0.0`, `funding_per_bar=0.0`, `commission_rate=0.00055`, `funding_rate_per_bar=0.00001`.

All fixed delayed close-stop candidates were early-falsified on required quarter `2024q1`:

| Candidate | 2024q1 status | Net profit | Profit factor | Max drawdown | Blockers |
| --- | --- | ---: | ---: | ---: | --- |
| `delayed-close-stop-1p0-after-4-hold-16` | fail | 170047.52 | 1.4670 | -0.9012 | max_drawdown_below_threshold |
| `target-3p0-delayed-close-stop-1p0-after-4-hold-32` | fail | 203572.40 | 1.5797 | -0.8928 | max_drawdown_below_threshold |
| `close-target-2p0-delayed-close-stop-1p0-after-4-hold-32` | fail | 136838.00 | 1.3884 | -1.4064 | max_drawdown_below_threshold |

Final verdict: falsified/negative evidence. Delayed close-stop improved `2024q1` net/PF relative to the `5/8` reference but did not solve max drawdown, so it cannot reach realistic-cost `8/8`; remaining quarters are recorded as blocked/not run after early falsification and are not counted as passes. No success notification is allowed for this result.
