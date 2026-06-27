# Proposal

## Why

The current BTCUSDT breakout reference `conservative-v1-m15-slope-positive-max-trades-8` remains `5/8` over the required quarterly windows `2023q1..2024q4`. The archived reference scorecard records passes in `2023q1`, `2023q2`, `2023q3`, `2023q4`, and `2024q3`, with failures in `2024q1`, `2024q2`, and `2024q4`. Key blockers are unchanged configured thresholds: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, and `require_no_feed_gaps=true`.

Archived path-risk/exit work has falsified fixed holds, intrabar stops/targets, close-confirmed stops, delayed close stops, break-even/trailing-only exits, partial/protected partial exits, realized drawdown guards, occupancy holds, large target exits, and fixed exposure scaling. The remaining useful local evidence is that large-target profiles can make `2024q1` strongly net/PF positive but still fail drawdown. This change tests a distinct profit-lock mechanism: keep large-target upside available, but activate trailing only after a larger favorable excursion so profitable paths can be locked before they reverse into large realized drawdowns.

## What Changes

Add a small fixed set of disabled-by-default BTCUSDT research-only profit-lock trailing exit profiles derived from `conservative-v1-m15-slope-positive-max-trades-8`:

- `conservative-v1-m15-slope-positive-max-trades-8-target-3p0-trail-1p5-giveback-1p0-hold-32`
- `conservative-v1-m15-slope-positive-max-trades-8-target-4p0-trail-2p0-giveback-1p0-hold-32`
- `conservative-v1-m15-slope-positive-max-trades-8-close-target-2p0-trail-1p5-giveback-1p0-hold-32`

The implementation SHALL preserve BTCUSDT default behavior unless one of the explicit profile names is selected, use only public cached OHLCV data, leave entry filters/thresholds/costs unchanged, and record exit profile settings separately from feature/regime/confirmation/risk settings.

## Pre-change quarterly scorecard

Artifact: `artifacts/realistic-cost-profile-search/conservative-v1-m15-slope-positive-max-trades-8/scorecard.csv` (baseline/current reference rows).

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

Reference score: `5/8`; failing quarters: `2024q1`, `2024q2`, `2024q4`. Primary blocker for this slice: `2024q1` drawdown while preserving net/PF from large-target behavior; if `2024q1` fails under realistic costs, the candidate cannot reach `8/8`.

## Success Criteria

- The named profiles map to deterministic exit settings and remain disabled unless explicitly selected.
- BTCUSDT default/reference behavior and supported profile validation remain unchanged.
- Each candidate is evaluated against the required quarterly scorecard `2023q1..2024q4`, unless a candidate is early-falsified by a failed required realistic-cost quarter that makes `8/8` impossible.
- Success requires one candidate to reach `8/8` with unchanged configured thresholds and realistic costs.
- If no candidate reaches `8/8`, archive as falsified/negative research evidence with scorecard artifact paths and do not send success notification.

## Non-goals

No live trading, production approval, private API/account access, private data, order book/DOM/L2/taker-flow, ML, broad optimization, asset-universe change, threshold weakening, push, MR, merge, or cloud delivery.
