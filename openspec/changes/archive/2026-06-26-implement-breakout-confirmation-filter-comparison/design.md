# Design

## Baseline
Use the fixed current best profile as the reference:

`conservative-v1-m15-slope-positive-max-trades-8`

Reference status before this change:

- passed: 5/8
- failed: 3/8
- hypothesis_supported: false

The previous volatility-regime filter comparison is treated as negative evidence for simple ATR/body threshold blocking. This change tests a different mechanism: false-breakout confirmation.

## Confirmation Semantics
A confirmation profile SHALL not enter at the original breakout bar if it needs later evidence. Instead:

1. A candidate breakout is detected at bar `t` using the existing signal/score path.
2. The engine records a pending candidate with the breakout level/range context available at `t`.
3. Confirmation is evaluated only as subsequent bars close.
4. If confirmation succeeds at bar `t+n`, the entry is placed at the earliest executable bar after confirmation according to the existing backtest execution convention.
5. If confirmation fails before success, the candidate is cancelled and counted with a deterministic skip/cancel reason.

This preserves no-lookahead semantics because the engine never enters at `t` using information from `t+1` or later.

## Fixed Profiles
### Reference
`conservative-v1-m15-slope-positive-max-trades-8`

Existing best profile with no confirmation delay.

### confirm-close-1
`conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1`

Require one confirmed close above the breakout level before entry.

### confirm-close-2
`conservative-v1-m15-slope-positive-max-trades-8-confirm-close-2`

Require two consecutive confirmed closes above the breakout level before entry.

### confirm-close-1-closepos70
`conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-closepos70`

Require one confirmed close above the breakout level and require the confirmation bar close position to be at least 0.70 within its high-low range:

`(close - low) / (high - low) >= 0.70`

If `high == low`, the close-position condition fails safely.

### confirm-close-1-no-return-inside-range
`conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-no-return-inside-range`

Require one confirmed close above the breakout level and cancel the candidate if a confirmation bar closes back inside the pre-breakout range before confirmation succeeds.

## Data and State Requirements
Use only data already present in the backtest dataset:

- M15 OHLCV execution bars.
- Existing public market-data provenance.
- Existing H1/H4/D1 context remains allowed where already used by the baseline profile, but confirmation itself must be expressible from M15 OHLCV.

No order book, footprint, стакан, DOM, L2 depth, trade tape, or private account data is allowed.

## Reporting
Batch summaries SHALL keep separate fields for:

- `gate_profile`
- `feature_filter_profile`
- `risk_control_profile`
- `confirmation_filter_profile`
- `confirmation_filter_settings_json`
- `confirmation_filter_skip_counts_json`

Confirmation skip/cancel reasons SHOULD be machine-readable, for example:

- `skipped_confirmation_close_not_above_breakout`
- `skipped_confirmation_close_position_below_min`
- `skipped_confirmation_returned_inside_range`
- `skipped_confirmation_expired`

The exact reason set may be adjusted during implementation if tests document the final codes.

## Experiment Plan
Run quarterly 2023-2024 BTCUSDT public-data batches for the required profiles using the existing market data directory if available.

Compare against the reference:

- passed/failed window count
- hypothesis_supported
- total trade count
- total net profit
- worst max drawdown
- remaining failed windows and blockers
- confirmation skip/cancel counts

## Decision Rule
This change supports the confirmation hypothesis only if a confirmation profile improves the reference and ideally reaches `hypothesis_supported=true`. If no confirmation profile improves the 5/8 reference, the hypothesis is not supported in this form and the result should guide the next research step.
