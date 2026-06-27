# Proposal

## Why
The BTCUSDT reference `conservative-v1-m15-slope-positive-max-trades-8` remains `5/8` over the required quarterly `2023q1..2024q4` scorecard under unchanged configured research thresholds: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, and `require_no_feed_gaps=true`.

Pre-change reference scorecard from `artifacts/realistic-cost-profile-search/conservative-v1-m15-slope-positive-max-trades-8/scorecard.csv`:

| Quarter | Status | Key blockers |
| --- | --- | --- |
| `2023q1` | pass | none |
| `2023q2` | pass | none |
| `2023q3` | pass | none |
| `2023q4` | pass | none |
| `2024q1` | fail | `net_profit_below_threshold`, `profit_factor_below_threshold`, `max_drawdown_below_threshold` |
| `2024q2` | fail | `net_profit_below_threshold`, `profit_factor_below_threshold`, `max_drawdown_below_threshold` |
| `2024q3` | pass | none |
| `2024q4` | fail | `max_drawdown_below_threshold` |

Archived exit/path-risk slices show that large targets can restore positive `2024q1` net/PF, but drawdown remains the primary blocker. The prior occupancy-hold slice tested occupancy with `hold-8`, `target-2p0-hold-16`, and `target-3p0-hold-32`; it did not test the strongest observed large-target family (`target-4p0-hold-32` or close-confirmed `close-target-2p0-hold-32`) under honest one-active-position occupancy. This slice tests that missing combination without changing entries, thresholds, costs, or adding new market/data dimensions.

## What Changes
Add fixed BTCUSDT research-only profile names that combine existing one-position occupancy gating with existing large-target exit semantics:

- `conservative-v1-m15-slope-positive-max-trades-8-occupancy-target-4p0-hold-32`
- `conservative-v1-m15-slope-positive-max-trades-8-occupancy-close-target-2p0-hold-32`

The implementation SHALL:

- reuse existing `block_overlapping_positions` occupancy behavior and existing target/close-target exit resolution;
- keep BTCUSDT `M15` execution with `H1/H4/D1` context metadata;
- keep public unauthenticated cached Bybit OHLCV only;
- keep realistic costs `spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055`, and `funding_rate_per_bar=0.00001`;
- evaluate the primary failing quarter `2024q1` first and promote only a `2024q1` pass to full `2023q1..2024q4`;
- record per-quarter status, blockers, metrics, and artifact paths;
- archive as falsified/negative evidence if no candidate reaches realistic-cost `8/8`.

## Success Criteria
- The new profile names serialize deterministic gate, risk-control, exit-profile, and occupancy settings.
- Default BTCUSDT behavior remains unchanged when these profile names are not selected.
- `2024q1` early-falsification artifacts are produced for each candidate with unchanged thresholds and realistic costs.
- A candidate is successful only if the full quarterly scorecard is `8/8`; anything below `8/8` is negative evidence, not success.

## Non-goals
No entry filters, volatility/regime filters, confirmation filters, ML, order book/DOM/L2/taker-flow, private/live API, production approval, threshold weakening, dynamic optimization, altcoin/universe scope, push, MR, merge, or cloud delivery.
