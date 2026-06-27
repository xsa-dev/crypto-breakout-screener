# Proposal

## Why
The current BTCUSDT reference profile `conservative-v1-m15-slope-positive-max-trades-8` remains `5/8` over `2023q1..2024q4`, with failures in `2024q1`, `2024q2`, and `2024q4`. The configured thresholds remain unchanged: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, and `require_no_feed_gaps=true`.

Archived path-risk/exit evidence shows that fixed extended holds, break-even/trailing exits, and asymmetric intrabar ATR stop/target exits did not reach `8/8` after realistic costs. The microscopic `0.01 ATR` intrabar stop reached baseline `8/8` but was falsified by realistic costs. A less noise-sensitive path-risk hypothesis remains unresolved: close-confirmed adverse exits can cut failed-window drawdowns only after the market closes below an ATR threshold, avoiding the intrabar stop churn that made tight stops cost-sensitive while still acting earlier than long fixed holds.

## What Changes
Implement and evaluate exactly these named research-only close-confirmed exit profiles for the existing reference:

- `conservative-v1-m15-slope-positive-max-trades-8-close-stop-0p5-hold-8`
- `conservative-v1-m15-slope-positive-max-trades-8-close-stop-1p0-hold-16`
- `conservative-v1-m15-slope-positive-max-trades-8-close-stop-0p5-close-target-2p0-hold-16`

The implementation SHALL:

- preserve entry selection, lifecycle gates, M15 slope feature filter, max-trades risk control, regime filters, confirmation filters, and research thresholds unless one of these explicit named exit profiles is selected;
- evaluate close-confirmed exits only after a trade exists using post-entry M15 bar closes and entry-time ATR;
- record close-stop and close-target settings/reasons in JSON/CSV artifacts separately from gates, filters, risk controls, and verdicts;
- run the exact eight required windows `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, and `2024q4`;
- evaluate both baseline and realistic-cost results where success requires `8/8` after realistic costs (`spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055`, and `funding_rate_per_bar=0.00001`);
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

Baseline score: `5/8`; failing quarters: `2024q1`, `2024q2`, `2024q4`. Primary shared failure mechanism for this change: adverse path risk after entry, especially drawdown excursions, without using entry filters or weakening thresholds.

## Success Criteria
- The new exit profile settings are disabled by default and do not change default/reference behavior.
- Each candidate is fixed, named, serialized in JSON/CSV summaries, and does not rely on broad parameter search.
- Quarterly scorecards include exactly the eight required windows.
- Configured thresholds remain unchanged.
- A success notification is sent only if a candidate reaches `8/8` after realistic costs.
- If the best candidate remains below `8/8`, tasks and artifacts record falsified/negative evidence, no success notification is sent, and the change is archived.

## Non-goals
- No live trading, production approval, broker/private API access, order book/стакан/DOM/L2/taker-flow, ML, broad optimization, push, MR, merge, or cloud delivery.
- No new entry filters, volatility filters, confirmation filters, production risk changes, martingale/averaging, or threshold weakening.
- No counting baseline-only `8/8` as robust success.
