# Design

## Context
Reference before this change:

- profile: `conservative-v1-m15-slope-positive-max-trades-8`
- required windows: `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, `2024q4`
- configured thresholds: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, `require_no_feed_gaps=true`
- archived reference artifact: `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/2396740c76d50b91/summary.json`
- current reference score: `5/8`; failing quarters are `2024q1`, `2024q2`, `2024q4`
- realistic-cost success condition: `8/8` after `spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055` per side, and `funding_rate_per_bar=0.00001`

## Hypothesis and mechanism
The selected mechanism is target-only post-entry profit capture. Earlier attempts that paired stops and targets or focused on adverse exits were falsified under realistic costs. This slice tests whether favorable continuation can be harvested with deterministic target exits while leaving adverse movement to the fixed holding fallback instead of introducing additional stop churn.

This is distinct from archived attempts:

- not a fixed-hold-only profile, because favorable target hits can close early;
- not an asymmetric ATR stop/target pair, because there is no new adverse stop;
- not break-even/trailing, because there is no stateful stop movement after favorable excursion;
- not close-confirmed stop, because only favorable target exits are added.

## Candidate set
- `target-1p0-hold-8`: intrabar favorable target at `entry_price + 1.0 * entry_time_ATR`, otherwise close at 8-bar horizon.
- `target-2p0-hold-16`: larger intrabar favorable target at `entry_price + 2.0 * entry_time_ATR`, otherwise close at 16-bar horizon.
- `close-target-1p0-hold-8`: less wick-sensitive favorable close-confirmed target at `entry_price + 1.0 * entry_time_ATR`, otherwise close at 8-bar horizon.

These candidates are fixed, named, and not an optimizer. If none reaches realistic-cost `8/8`, the hypothesis is falsified for this slice.

A candidate may be early-falsified once a required quarter fails under realistic costs, because `8/8` is then impossible. Any remaining required quarters must stay visible in the scorecard as blocked/not run after early falsification and must not be counted as passes.

## Engine semantics
Update `BacktestExitProfileConfig` validation so `target_atr` may be configured without `stop_atr`. `stop_atr` may also remain configured with `target_atr` for existing paired profiles. Existing paired profiles keep their current behavior.

When target-only is configured:

1. Use only already accepted trades; do not affect level detection, scoring, gates, filters, sizing, or entry selection.
2. Read entry-time ATR from the existing feature snapshot. If ATR is unavailable or non-positive, fall back to the configured maximum-hold close and record `missing_entry_atr_fixed_holding_close`.
3. For each post-entry bar up to `fixed_holding_bars`:
   - intrabar target profile exits when `bar.high >= entry_price + target_atr * ATR`;
   - close-confirmed target profile exits when `bar.close >= entry_price + close_target_atr * ATR`.
4. If no target is reached, use the existing maximum-hold close fallback.
5. Serialize target settings and `exit_reason` in trade metadata and existing exit-profile counters.

## No-lookahead boundary
Target-only profiles use entry-time ATR and post-entry bars only after the trade exists. They do not prefilter entries or use future labels before trade creation. Reference behavior without a selected target-only profile must remain unchanged.

## Verification
- Strict OpenSpec validation before source implementation.
- Targeted unit tests for target-only config validation, intrabar target-only exit, close-confirmed target-only exit, missing ATR fallback, and unchanged default/reference selection.
- Quarterly batch command pattern:
  `env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.crypto_batch --preset quarterly-2023-2024 --gate-profile <profile> --reuse-market-data --output-dir artifacts/target-only-exit-profile-comparison/<profile> --market-data-dir artifacts/batch-market-data`
- Realistic-cost summary command:
  `env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.realistic_cost_profile_search <summary> ... --output-dir artifacts/target-only-exit-profile-comparison-summary/realistic-cost`
- Project checks: targeted pytest, full pytest, ruff, pyright, OpenSpec validate all, `git diff --check`, duplicate spec/archive-name check.
