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
The selected mechanism is close-confirmed post-entry path-risk control. Earlier attempts falsified:

- fixed holds: longer holds reduced turnover but worsened many windows;
- intrabar ATR stops/targets: moderate stops failed baseline and realistic costs, while the microscopic tight stop was baseline-only and cost-sensitive;
- break-even/trailing: path-risk protection did not overcome realistic costs.

Close-confirmed exits differ because they respond only to bar closes after entry. They should be less sensitive to wick noise and intrabar stop churn than tight stops, but still exit before long-hold drawdowns when the adverse move persists into the close. The main target blockers are `2024q1` and `2024q2` net/PF/drawdown plus `2024q4` drawdown.

## Candidate set
- `close-stop-0p5-hold-8`: exit at the first post-entry M15 close at or below `entry_price - 0.5 * entry_time_ATR`, otherwise close at the 8-bar horizon.
- `close-stop-1p0-hold-16`: wider adverse confirmation and longer horizon to test whether avoiding noise stops preserves enough gross edge.
- `close-stop-0p5-close-target-2p0-hold-16`: pair the 0.5 ATR close stop with a close-confirmed 2.0 ATR profit exit over a longer horizon to test whether gross edge per trade can improve without intrabar target churn.

These candidates are fixed, named, and not an optimizer. If none reaches realistic-cost `8/8`, the hypothesis is falsified for this slice.

## Engine semantics
Extend `BacktestExitProfileConfig` with disabled-by-default optional fields:

- `close_stop_atr: float | None`
- `close_target_atr: float | None`

When either field is configured:

1. Use only already accepted trades; do not affect level detection, scoring, gates, filters, sizing, or entry selection.
2. Read entry-time ATR from the existing feature snapshot. If ATR is unavailable or non-positive, fall back to the configured maximum-hold close and record `missing_entry_atr_fixed_holding_close`.
3. For each post-entry bar in order up to `fixed_holding_bars`, evaluate close-confirmed thresholds using the bar close:
   - stop threshold: `entry_price - close_stop_atr * ATR`;
   - target threshold: `entry_price + close_target_atr * ATR`.
4. If both close thresholds are theoretically true in the same bar, use conservative stop-first ordering.
5. If no close threshold is reached, use the existing maximum-hold close fallback.
6. Serialize `exit_profile_close_stop_atr`, `exit_profile_close_target_atr`, and `exit_reason` in trade metadata and existing exit-profile counters.

Existing intrabar stop/target, break-even, and trailing semantics remain unchanged.

## No-lookahead boundary
The close-confirmed profile uses entry-time ATR and post-entry bar closes only after the trade exists. It does not prefilter entries or use future labels before trade creation. Reference behavior without a selected close-confirmed profile must remain unchanged.

## Verification
- Strict OpenSpec validation before source implementation.
- Targeted unit tests for close-confirmed stop/target semantics, missing ATR fallback, profile resolution, and unchanged default/reference selection.
- Quarterly batch command pattern:
  `env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.crypto_batch --preset quarterly-2023-2024 --gate-profile <profile> --reuse-market-data --output-dir artifacts/close-confirmed-exit-profile-comparison/<profile> --market-data-dir artifacts/batch-market-data`
- Realistic-cost summary command:
  `env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.realistic_cost_profile_search <summary> ... --output-dir artifacts/close-confirmed-exit-profile-comparison-summary/realistic-cost`
- Project checks: targeted pytest, full pytest, ruff, pyright, OpenSpec validate all, `git diff --check`, duplicate spec/archive-name check.
