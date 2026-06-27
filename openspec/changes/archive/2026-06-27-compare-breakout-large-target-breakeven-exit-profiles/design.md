# Design

## Hypothesis
A large-target BTCUSDT exit can preserve the favorable excursions seen in `2024q1` while a break-even arm after `+1.0 ATR` prevents some winners from reversing into large realized losses. The primary blocker is `2024q1` drawdown/net/PF, with `2024q2` negative expectancy and `2024q4` drawdown as mandatory follow-up gates.

## Candidate profiles
The change tests exactly these fixed names:

1. `conservative-v1-m15-slope-positive-max-trades-8-target-3p0-breakeven-1p0-hold-32`
   - `fixed_holding_bars=32`
   - `target_atr=3.0`
   - `breakeven_after_atr=1.0`
2. `conservative-v1-m15-slope-positive-max-trades-8-target-4p0-breakeven-1p0-hold-32`
   - `fixed_holding_bars=32`
   - `target_atr=4.0`
   - `breakeven_after_atr=1.0`
3. `conservative-v1-m15-slope-positive-max-trades-8-close-target-2p0-breakeven-1p0-hold-32`
   - `fixed_holding_bars=32`
   - `close_target_atr=2.0`
   - `breakeven_after_atr=1.0`

No parameter search is added. The engine already supports `target_atr`, `close_target_atr`, and `breakeven_after_atr`; this change only wires fixed profile names and tests their scorecards.

## Quarterly scorecard protocol
Before implementation, the reference scorecard is fixed as `5/8`: passes `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q3`; fails `2024q1`, `2024q2`, `2024q4`.

Run `2024q1` first for each candidate because archived large-target variants are primarily blocked by `2024q1` path drawdown. If a candidate fails `2024q1`, mark all other quarters blocked for that candidate as `not_run_after_2024q1_early_falsification`. If a candidate passes `2024q1`, promote it to the full eight-quarter scorecard.

Configured realistic costs and thresholds are unchanged:

- `spread=1.0`
- `slippage_per_unit=0.5`
- `commission_rate=0.00055`
- `funding_rate_per_bar=0.00001`
- `min_trade_count=1`
- `min_net_profit=0.0`
- `min_profit_factor=1.0`
- `min_max_drawdown=-0.35`
- `require_no_feed_gaps=true`

## Artifacts
Write combined comparison evidence under `artifacts/large-target-breakeven-exit-profile-comparison/early-falsified/` or equivalent full-run output:

- `summary.json`
- `scorecard.csv`
- per-candidate/per-window batch summary artifact paths

## Risks
- Break-even after `+1.0 ATR` may exit too many trades flat after costs, preserving drawdown but damaging net/PF.
- Large targets may still allow drawdown before break-even activation.
- Because this is exit-only, it cannot remove bad entries; failing `2024q2` remains likely negative evidence.
