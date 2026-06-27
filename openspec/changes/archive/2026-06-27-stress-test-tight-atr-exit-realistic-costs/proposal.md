# Proposal

## Why
The archived `implement-breakout-path-risk-exit-profile-comparison` change found an `8/8` BTCUSDT quarterly profile:

`conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p01-target-2p0`

Its scorecard passed all 2023q1..2024q4 windows under the existing explicit cost model, but that cost model is per-unit (`spread`, `slippage_per_unit`, `commission_per_unit`, `funding_per_bar`). The discovered profile uses a very tight `0.01 ATR` stop and wins with a low win rate plus rare large targets, so it may be highly sensitive to realistic notional trading fees, spread/slippage stress, and funding. Passing the original quarterly thresholds is useful research evidence, but it is not enough to treat the profile as robust.

## What Changes
Add research-only realistic cost stress testing for the discovered tight ATR exit profile:

- extend `BacktestCostModel` with optional notional commission/funding rates while preserving existing default behavior;
- expose batch-runner cost parameters so quarterly runs can be repeated with explicit stress assumptions;
- record cost settings in batch summary artifacts;
- run the successful profile across the same 2023q1..2024q4 quarterly windows under multiple realistic/stressed cost scenarios;
- report whether `8/8` survives without weakening configured research thresholds.

## Baseline Evidence
Archived successful artifact:

`artifacts/exit-profile-comparison/crypto/BTCUSDT/f7f80591545417ed/summary.json`

Baseline result:

- profile: `conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p01-target-2p0`
- score: `8/8`
- total net profit: `98652.00485712058`
- total trades: `3948`
- mean profit factor: `4.619254304970152`
- worst max drawdown: `-0.08265596607356647`
- mean win rate: `0.07476935649512526`
- mean sharpe ratio: `0.15545032470848924`
- exit settings: `fixed_holding_bars=1`, `stop_atr=0.01`, `target_atr=2.0`

## Success Criteria
- Existing default/per-unit cost behavior remains deterministic and backwards compatible.
- Batch runner can explicitly run quarterly BTCUSDT experiments with notional commission and funding assumptions.
- Batch summary JSON/CSV records the cost model used for each stress run.
- The discovered tight ATR profile is rerun over exactly `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, `2024q4`.
- Stress results record per-quarter pass/fail, blockers, net profit, drawdown, profit factor, trade count, cost totals, artifact paths, and final verdict.
- Thresholds are not weakened: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, `require_no_feed_gaps=true`.
- If realistic costs break `8/8`, archive the change as falsified/negative robustness evidence with exact artifacts.
- If realistic costs preserve `8/8`, archive the change as robustness evidence and identify the next risk check rather than claiming production approval.

## Non-goals
- No live trading, production approval, broker API, balances, orders, positions, `.env`, private endpoints, push, MR, merge, or cloud delivery.
- No weakening thresholds or reducing the quarterly window set.
- No new entry filters, no-trade filters, regime filters, confirmation filters, ML, or broad parameter search.
- No current exchange-fee guarantee; stress assumptions are explicit local research assumptions.
