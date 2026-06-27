# Proposal

## Why
The current BTCUSDT reference profile `conservative-v1-m15-slope-positive-max-trades-8` remains `5/8` over the required quarterly windows `2023q1..2024q4`, with failures in `2024q1`, `2024q2`, and `2024q4`. The configured research thresholds remain unchanged: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, and `require_no_feed_gaps=true`.

Archived path-risk/exit work has falsified fixed holds, small and large target-only exits, ATR stop/target pairs, close-confirmed exits, break-even/trailing exits, unprotected partial exits, and protected residual partial exits. The strongest remaining path-risk blocker is realized equity drawdown after otherwise profitable larger-target runs: recent large-target realistic-cost checks made `2024q1` net/PF strongly positive but still failed max drawdown. This change tests a narrow realized-state drawdown guard layered on large-target exits to stop taking new trades after a configured peak-to-trough equity drawdown is reached, without changing entry scoring, thresholds, private data scope, or live behavior.

## What Changes
Implement and evaluate exactly these fixed research-only profiles:

- `conservative-v1-m15-slope-positive-max-trades-8-target-3p0-hold-32-drawdown-30pct`
- `conservative-v1-m15-slope-positive-max-trades-8-target-4p0-hold-32-drawdown-30pct`
- `conservative-v1-m15-slope-positive-max-trades-8-close-target-2p0-hold-32-drawdown-30pct`

The implementation SHALL:

- preserve entry scoring, M15 slope feature filter, max-trades risk control, target/holding exit semantics, confirmation/regime filters, and configured research thresholds unless one of these explicit named profiles is selected;
- apply the drawdown guard only from already-realized equity state available before a new trade is created;
- record the guard threshold and skip counts in existing batch JSON/CSV gate/risk/exit artifacts;
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

Baseline score: `5/8`; failing quarters: `2024q1`, `2024q2`, `2024q4`. Primary mechanism for this change: realized equity drawdown guard on large-target exits, targeting the max-drawdown blocker without adding new entry filters or weakening thresholds.

## Success Criteria
- The new guard is disabled by default and does not change default/reference behavior.
- Each candidate is fixed, named, serialized in JSON/CSV summaries, and does not rely on broad parameter search.
- Drawdown guard decisions use only realized equity state before entry; no current/future trade outcome is inspected to decide whether to skip.
- Quarterly scorecards include exactly the eight required windows, with any not-run windows after early falsification marked blocked rather than counted as pass.
- Configured thresholds and realistic-cost settings remain unchanged.
- A success notification is sent only if a candidate reaches `8/8` after realistic costs.
- If the best candidate remains below `8/8`, tasks and artifacts record falsified/negative evidence, no success notification is sent, and the change is archived.

## Final quarterly evidence
Final realistic-cost candidate artifact:

- Combined summary: `artifacts/equity-drawdown-guard-profile-comparison-summary/early-falsified/summary.json`
- Scorecard CSV: `artifacts/equity-drawdown-guard-profile-comparison-summary/early-falsified/scorecard.csv`

| Candidate | Required quarter run | Status | Net profit | Profit factor | Max drawdown | Blockers |
| --- | --- | --- | ---: | ---: | ---: | --- |
| `target-3p0-hold-32-drawdown-30pct` | 2024q1 | fail | 5411.55 | 1.3743 | -0.4626 | max_drawdown_below_threshold |
| `target-4p0-hold-32-drawdown-30pct` | 2024q1 | fail | 7025.37 | 1.4783 | -0.4597 | max_drawdown_below_threshold |
| `close-target-2p0-hold-32-drawdown-30pct` | 2024q1 | fail | 4296.02 | 1.3222 | -0.4788 | max_drawdown_below_threshold |

Final verdict: falsified/negative evidence. Score did not reach realistic-cost `8/8`; all candidates are early-falsified by required window `2024q1`, and remaining windows are recorded as blocked/not run after early falsification.

## Non-goals
- No live trading, production approval, broker/private API access, order book/стакан/DOM/L2/taker-flow, ML, broad optimization, push, MR, merge, or cloud delivery.
- No new entry filters, volatility filters, confirmation filters, martingale/averaging, or threshold weakening.
- No counting baseline-only `8/8` as robust success.
