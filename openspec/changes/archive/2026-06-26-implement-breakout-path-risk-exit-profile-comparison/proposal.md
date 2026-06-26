# Proposal

## Why
The current BTCUSDT breakout research reference remains `conservative-v1-m15-slope-positive-max-trades-8` with 5/8 quarterly windows passed over 2023q1..2024q4. The known failing quarters are `2024q1`, `2024q2`, and `2024q4`; the archived reference verdict is `hypothesis_supported=false`.

Archived entry filters, volatility/regime filters, risk controls, and confirmation filters did not improve the 5/8 reference. The latest path-risk diagnostics show failed windows are dominated by noisy favorable/adverse ordering rather than lack of movement:

- failed-window +1 ATR favorable-before-1 ATR adverse ratios are only ~0.13/0.24/0.36/0.45/0.48 across 1/2/4/8/16 M15 bars;
- failed windows still reach break-even at material rates by 8/16 bars (~0.56/~0.69), but break-even touch-after-reach is high (~0.49/~0.63);
- trailing giveback touch rates after +1 ATR are very high, so trailing/break-even alone is risky;
- `2024q4` is drawdown-blocked while `2024q1` and `2024q2` fail net profit, profit factor, and drawdown.

The next bounded hypothesis is that a small, fixed research-only exit profile comparison can improve the current one-bar close lifecycle by changing exit timing/path-risk handling after a trade is already entered, without adding entry/no-trade filters or weakening research thresholds.

## What Changes
Implement fixed BTCUSDT batch comparison support for research-only exit profiles on top of the existing reference:

- reference: `conservative-v1-m15-slope-positive-max-trades-8` (unchanged one-bar close);
- fixed holding profiles that close after a fixed number of M15 bars;
- fixed ATR stop/target path profiles that use entry-time ATR and deterministic OHLCV intrabar ordering;
- one tight protective-stop profile that preserves the one-bar lifecycle while testing whether immediate adverse path containment can clear the remaining 2024 drawdown blockers;
- batch summary fields that keep exit profile settings/results separate from gates, feature filters, regime filters, confirmation filters, realized metrics, and verdicts.

The comparison SHALL run over exactly the eight quarterly windows: `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, `2024q4`.

## Pre-implementation quarterly scorecard
Reference command/artifact:

`uv run python -m src.app.breakout.experiments.crypto_batch --preset quarterly-2023-2024 --gate-profile conservative-v1-m15-slope-positive-max-trades-8 --output-dir artifacts/path-risk-exit-diagnostics --market-data-dir artifacts/batch-market-data --path-risk-diagnostics`

Artifact: `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/2396740c76d50b91/path-risk-window-summary.csv`

| Quarter | Status | Blockers |
| --- | --- | --- |
| 2023q1 | pass | none |
| 2023q2 | pass | none |
| 2023q3 | pass | none |
| 2023q4 | pass | none |
| 2024q1 | fail | net_profit_below_threshold; profit_factor_below_threshold; max_drawdown_below_threshold |
| 2024q2 | fail | net_profit_below_threshold; profit_factor_below_threshold; max_drawdown_below_threshold |
| 2024q3 | pass | none |
| 2024q4 | fail | max_drawdown_below_threshold |

Baseline score: 5/8. Primary shared failure mechanism for this change: adverse path risk after entry and potentially suboptimal one-bar exit timing in `2024q1`, `2024q2`, and `2024q4`.

## Success Criteria
- The implementation preserves reference behavior when no exit profile is selected.
- Named fixed exit profiles are disabled by default and are research-only.
- Exit profile logic uses only entry-time data plus post-entry bars after the trade exists; it does not affect entry selection, sizing, gates, confirmation, or feature filters.
- Batch CSV/JSON summaries expose `exit_profile`, `exit_profile_settings_json`, and any exit-profile counters separately.
- A real quarterly 2023q1..2024q4 BTCUSDT batch is run for the selected fixed profiles.
- Success requires 8/8 quarterly windows passing configured research thresholds without weakening thresholds. If no fixed profile reaches 8/8, the change must record the exact failed scorecards and remain unfinished unless a true external blocker prevents further local evaluation.
- OpenSpec validation, tests, lint, typecheck, and git diff hygiene pass before any archive/commit.

## Final quarterly evidence
Final successful profile command:

`uv run python -m src.app.breakout.experiments.crypto_batch --preset quarterly-2023-2024 --gate-profile conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p01-target-2p0 --output-dir artifacts/exit-profile-comparison --market-data-dir artifacts/batch-market-data`

Artifacts:

- Summary JSON: `artifacts/exit-profile-comparison/crypto/BTCUSDT/f7f80591545417ed/summary.json`
- Summary CSV: `artifacts/exit-profile-comparison/crypto/BTCUSDT/f7f80591545417ed/summary.csv`

| Quarter | Status | Trade count | Net profit | Max drawdown | Profit factor | Blockers |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 2023q1 | pass | 519 | 4194.5885714296455 | -0.03807927672682414 | 2.925475825744868 | none |
| 2023q2 | pass | 452 | 4155.29914285813 | -0.022502515879433048 | 3.416605006204932 | none |
| 2023q3 | pass | 384 | 8162.181714286446 | -0.007311400269485042 | 8.454700790470287 | none |
| 2023q4 | pass | 568 | 8412.557142857826 | -0.020643385098593158 | 3.997953438173451 | none |
| 2024q1 | pass | 554 | 15817.208285709814 | -0.05452124529298541 | 3.9956070383670985 | none |
| 2024q2 | pass | 432 | 16415.778857136058 | -0.04555509776740516 | 4.834982592957861 | none |
| 2024q3 | pass | 520 | 22273.87457142651 | -0.08265596607356647 | 5.406883672571175 | none |
| 2024q4 | pass | 519 | 19220.516571416156 | -0.044575576181834324 | 3.921826075271541 | none |

Final score: 8/8 passed, `technical_pass=true`, `hypothesis_supported=true`. Configured research thresholds were unchanged: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, `require_no_feed_gaps=true`.

## Non-goals
- No live trading, production approval, full-auto enablement, private API, balances, orders, positions, `.env`, authorization headers, or private endpoints.
- No new entry filters, no-trade filters, volatility/regime filters, confirmation filters, or ML.
- No order book, стакан, DOM, L2 depth, footprint, taker-flow, or trade tape data.
- No automatic threshold optimization, broad parameter search, or weakening configured research thresholds.
- No new market, symbol, timeframe family, short-side strategy, or portfolio construction.
