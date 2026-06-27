# Proposal

## Why
The BTCUSDT reference `conservative-v1-m15-slope-positive-max-trades-8` remains `5/8` over the required quarterly windows `2023q1..2024q4` under the configured research thresholds: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, and `require_no_feed_gaps=true`.

Pre-change reference scorecard from `artifacts/realistic-cost-profile-search/conservative-v1-m15-slope-positive-max-trades-8/scorecard.csv`:

| Quarter | Status | Net profit | Profit factor | Max drawdown | Blockers |
| --- | --- | ---: | ---: | ---: | --- |
| `2023q1` | pass | 5614.00 | 1.1364 | -0.3157 | none |
| `2023q2` | pass | 7018.80 | 1.1949 | -0.3471 | none |
| `2023q3` | pass | 4324.80 | 1.1820 | -0.1866 | none |
| `2023q4` | pass | 7203.20 | 1.1232 | -0.2635 | none |
| `2024q1` | fail | -6187.60 | 0.9542 | -1.1749 | `net_profit_below_threshold`; `profit_factor_below_threshold`; `max_drawdown_below_threshold` |
| `2024q2` | fail | -483.60 | 0.9957 | -0.7581 | `net_profit_below_threshold`; `profit_factor_below_threshold`; `max_drawdown_below_threshold` |
| `2024q3` | pass | 28130.00 | 1.2489 | -0.2225 | none |
| `2024q4` | fail | 9230.40 | 1.0551 | -0.4225 | `max_drawdown_below_threshold` |

Archived exit/path-risk evidence shows: tight ATR stop reached baseline `8/8` but failed realistic notional-cost robustness; fixed holds, target-only exits, close stops, delayed close stops, trailing locks, partial/protected partial exits, occupancy exits, large targets, and exposure scaling failed to reach realistic-cost `8/8`. A missing simple path-risk variant remains: preserve large-target upside, but arm a break-even exit after favorable excursion so paths that move in favor and then reverse cannot become large losers. This is distinct from trailing locks because it does not ratchet behind the high, and distinct from the archived `breakeven-1p0-hold-8` because it combines break-even protection with the large-target/hold-32 family that made `2024q1` net/PF positive.

## What Changes
Add a small fixed set of disabled-by-default BTCUSDT research-only large-target + break-even exit profiles:

- `conservative-v1-m15-slope-positive-max-trades-8-target-3p0-breakeven-1p0-hold-32`
- `conservative-v1-m15-slope-positive-max-trades-8-target-4p0-breakeven-1p0-hold-32`
- `conservative-v1-m15-slope-positive-max-trades-8-close-target-2p0-breakeven-1p0-hold-32`

The implementation SHALL preserve BTCUSDT default behavior unless one of the explicit profile names is selected, use only public cached OHLCV data, leave entry filters/thresholds/costs unchanged, and record exit profile settings separately from feature/regime/confirmation/risk settings.

## Success Criteria
- The named profiles map to deterministic exit settings and remain disabled unless explicitly selected.
- BTCUSDT default/reference behavior and supported profile validation remain unchanged.
- Each candidate is evaluated against the required quarterly scorecard `2023q1..2024q4`, unless a candidate is early-falsified by a failed required realistic-cost quarter that makes `8/8` impossible.
- Success requires one candidate to reach `8/8` with unchanged configured thresholds and realistic costs (`spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055`, `funding_rate_per_bar=0.00001`).
- If no candidate reaches `8/8`, archive as falsified/negative research evidence with scorecard artifact paths and do not send success notification.

## Non-goals
No live trading, production approval, private API/account access, private data, order book/DOM/L2/taker-flow, ML, broad optimization, asset-universe change, threshold weakening, push, MR, merge, or cloud delivery.
