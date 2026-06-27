# Proposal

## Why
The current BTCUSDT reference profile `conservative-v1-m15-slope-positive-max-trades-8` remains `5/8` over the required quarterly windows `2023q1..2024q4`, with failures in `2024q1`, `2024q2`, and `2024q4`. The configured research thresholds remain unchanged: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, and `require_no_feed_gaps=true`.

Archived exit and path-risk slices show a consistent split: larger target/holding profiles can turn `2024q1` strongly net/PF positive under realistic costs, but fail max drawdown because the fixed `base_quantity=10.0` exposure keeps drawdown above the `-0.35` threshold. Tight stops and protected residual exits reduce path exposure too aggressively and become cost/negative-expectancy failures. This change tests a distinct bounded exposure/path-risk hypothesis: keep the favorable large-target exit mechanics, but evaluate fixed lower per-trade exposure profiles so drawdown is controlled without weakening thresholds or using broad parameter search.

## What Changes
Implement and evaluate exactly these fixed research-only profiles:

- `conservative-v1-m15-slope-positive-max-trades-8-target-3p0-hold-32-qty-0p5`
- `conservative-v1-m15-slope-positive-max-trades-8-target-4p0-hold-32-qty-0p5`
- `conservative-v1-m15-slope-positive-max-trades-8-close-target-2p0-hold-32-qty-0p5`

The implementation SHALL:

- preserve entry scoring, M15 slope feature filter, max-trades risk control, confirmation/regime filters, configured research thresholds, and default/reference behavior unless one of these explicit named profiles is selected;
- keep the large-target/holding exit mechanics fixed and already-supported, while setting only the candidate's `base_quantity` to `0.5` instead of the batch default `10.0`;
- serialize exposure settings (`base_quantity`, and default `initial_equity` when relevant), exit settings, cost settings, per-quarter metrics, and blockers in JSON/CSV artifacts;
- run the exact eight required windows `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, and `2024q4`, unless a candidate is early-falsified by a failed required realistic-cost quarter that makes `8/8` impossible;
- evaluate realistic-cost results where success requires `8/8` after `spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055`, and `funding_rate_per_bar=0.00001`;
- archive the change as falsified evidence if no candidate reaches realistic-cost `8/8`.

## Pre-change quarterly scorecard
Reference command/artifact:

`env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.crypto_batch --preset quarterly-2023-2024 --gate-profile conservative-v1-m15-slope-positive-max-trades-8 --output-dir artifacts/path-risk-exit-diagnostics --market-data-dir artifacts/batch-market-data --path-risk-diagnostics`

Artifact: `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/2396740c76d50b91/summary.json`

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

Baseline score: `5/8`; failing quarters: `2024q1`, `2024q2`, `2024q4`. Primary mechanism for this change: exposure-scaled large-target path risk, with `2024q1` as the first highest-impact drawdown blocker and `2024q2` as the key negative-expectancy blocker that must also turn positive for any `8/8` result.

## Success Criteria
- New profiles are disabled by default and do not change default/reference behavior.
- Each candidate is fixed, named, serialized in JSON/CSV summaries, and does not rely on broad parameter search.
- Quarterly scorecards include exactly the eight required windows, with any not-run windows after early falsification marked blocked rather than counted as pass.
- Configured thresholds and realistic-cost settings remain unchanged.
- A success notification is sent only if a candidate reaches `8/8` after realistic costs.
- If the best candidate remains below `8/8`, tasks and artifacts record falsified/negative evidence, no success notification is sent, and the change is archived.

## Final quarterly evidence
Final realistic-cost candidate artifact:

- Combined summary: `artifacts/scaled-exit-exposure-profile-comparison/early-falsified/summary.json`
- Scorecard CSV: `artifacts/scaled-exit-exposure-profile-comparison/early-falsified/scorecard.csv`

| Candidate | Required quarter run | Status | Net profit | Profit factor | Max drawdown | Blockers |
| --- | --- | --- | ---: | ---: | ---: | --- |
| `target-3p0-hold-32-qty-0p5` | 2024q2 | fail | -6109.27 | 0.7914 | -0.6674 | net_profit_below_threshold; profit_factor_below_threshold; max_drawdown_below_threshold |
| `target-4p0-hold-32-qty-0p5` | 2024q2 | fail | -3535.13 | 0.8814 | -0.4802 | net_profit_below_threshold; profit_factor_below_threshold; max_drawdown_below_threshold |
| `close-target-2p0-hold-32-qty-0p5` | 2024q2 | fail | -5277.63 | 0.8128 | -0.5979 | net_profit_below_threshold; profit_factor_below_threshold; max_drawdown_below_threshold |

Exploratory `2024q1` checks showed the fixed `qty-0p5` profiles can reduce the primary `2024q1` drawdown blocker enough to pass that quarter, but all candidates fail the next required blocker quarter `2024q2` under realistic costs. Final verdict: falsified/negative evidence. Score did not reach realistic-cost `8/8`; remaining windows are recorded as blocked/not run after `2024q2` early falsification and are not counted as passes.

## Non-goals
- No live trading, production approval, broker/private API access, order book/стакан/DOM/L2/taker-flow, ML, broad optimization, push, MR, merge, or cloud delivery.
- No new entry filters, volatility filters, confirmation filters, production risk changes, martingale/averaging, or threshold weakening.
- No counting baseline-only `8/8` as robust success.
