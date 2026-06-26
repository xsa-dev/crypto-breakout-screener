# Design

## Goal
Add deterministic research-only feature-filter profiles that test whether entry-time diagnostic signals can reduce drawdown enough for the BTCUSDT quarterly breakout hypothesis to pass.

This is a comparison/evidence change, not a production strategy approval.

## Current evidence
The archived diagnostics run shows:

- `conservative-v1` still fails 6/8 quarterly windows, mostly on max drawdown.
- M15 EMA slope is the strongest single diagnostic split:
  - negative: 3,237 trades, net PnL -24,607.60;
  - positive: 3,956 trades, net PnL 77,993.20.
- H1 trend alignment is also useful:
  - H1 short_or_flat: 2,661 trades, net PnL -4,132.80;
  - H1 long: 4,532 trades, net PnL 57,518.40.
- Candle body ratio `>0.75` is a weak bucket:
  - 1,222 trades, net PnL -6,559.20.

These are post-export diagnostics. Actual profile backtests are still required because applying filters during simulation changes lifecycle state, cooldowns, max trades per day, and daily stop-loss sequencing.

## Filter semantics
Feature filters must be evaluated only after ordinary setup scoring and before trade creation. They must use only the same no-lookahead entry feature snapshot values that are already computed from closed M15 bars and closed H1/H4/D1 context bars.

Feature filters must not read:

- next bars;
- exit price;
- trade outcome;
- future PnL or drawdown;
- future or not-yet-closed H1/H4/D1 candles;
- private exchange/account data.

Skipped entries should be recorded in deterministic skip counters and lifecycle/feature diagnostics where appropriate.

## Named research profiles
The implementation should support these named profiles for quarterly comparison:

1. `baseline`
   - Existing behavior, no research gates or feature filters.

2. `conservative-v1`
   - Existing lifecycle research gate profile.

3. `conservative-v1-m15-slope-positive`
   - `conservative-v1` plus M15 EMA slope filter.
   - Accept long entries only when `feature_ema_slope_atr > 0`.

4. `conservative-v1-h1-long`
   - `conservative-v1` plus H1 context trend filter.
   - Accept long entries only when `feature_context_H1_trend_alignment == "long"`.
   - Missing H1 context should skip the entry with an explicit reason for this profile.

5. `conservative-v1-m15-slope-positive-h1-long`
   - Both M15 positive slope and H1 long context.

6. `conservative-v1-m15-slope-positive-body-cap`
   - M15 positive slope plus candle body cap.
   - Accept entries only when `feature_candle_body_range_ratio <= 0.75`.

Optional implementation may include a breakout-distance exclusion profile only if it does not broaden the change or introduce optimization:

- exclude `0.5..1.0` ATR breakout distance bucket.

## Configuration shape
Prefer a typed research feature-filter config nested under backtest config, separate from lifecycle gates. It should be disabled by default and serializable in `parameter_snapshot`.

A minimal model may include:

- `require_m15_ema_slope_positive: bool = False`;
- `require_h1_trend_long: bool = False`;
- `max_candle_body_ratio: float | None = None` with positive bounds;
- possibly `excluded_breakout_distance_bucket: str | None = None` only if implemented explicitly.

Named batch profiles should expand to lifecycle gate config plus feature-filter config. Do not infer filters from arbitrary strings without validation.

## Batch comparison
The BTCUSDT quarterly batch runner should compare at least:

- `baseline`;
- `conservative-v1`;
- `conservative-v1-m15-slope-positive`;
- `conservative-v1-h1-long`;
- `conservative-v1-m15-slope-positive-h1-long`;
- `conservative-v1-m15-slope-positive-body-cap`.

The summary must keep the existing verdict logic and thresholds. A profile only supports the hypothesis if the existing batch verdict says so across the required windows.

The report should include:

- profile name;
- lifecycle gate settings;
- feature-filter settings;
- trade count;
- net profit;
- max drawdown;
- profit factor;
- win rate;
- failed/blocked windows;
- skip counters for feature-filter reasons;
- artifact references.

## Safety and scope boundaries
- Public unauthenticated BTCUSDT data only.
- M15 remains execution timeframe.
- H1/H4/D1 remain context datasets.
- No `.env`, private keys, authorization headers, balances, positions, orders, or private endpoints.
- No ML/boosting/neural-net dependency.
- No automated threshold/parameter optimization.
- No live trading or production approval.
- No default behavior change outside explicitly requested named profiles.

## Verification strategy
- Unit tests that default feature filters are disabled and preserve existing behavior.
- Unit tests for each enabled filter skip/pass condition using deterministic bars/context.
- No-lookahead regression for H1 context filters using open-time OHLCV timestamps and close-time availability.
- Batch profile tests confirming settings and summary fields are recorded.
- Targeted and full pytest, ruff, pyright, OpenSpec strict validation, and `git diff --check`.
- Real BTCUSDT quarterly public-data comparison if network/data is available; otherwise report the exact blocker and run fixture-based smoke.
