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
The selected mechanism is deterministic partial profit capture after entry. Previous target-only profiles closed the whole trade at the first favorable target and were falsified; previous stop/trailing profiles added adverse or giveback exits that did not survive realistic costs. This slice tests whether partial realization can reduce drawdown in the failed windows while preserving residual upside and without increasing trade count or adding new entry/no-trade filters.

## Candidate set
- `partial-50-target-1p0-hold-16`: exit 50% of quantity at intrabar `entry_price + 1.0 * entry_time_ATR`; close remaining 50% at the 16-bar fallback close.
- `partial-30-50-targets-1p0-2p0-hold-16`: exit 30% at intrabar `+1.0 ATR`, 50% at intrabar `+2.0 ATR`, and close the remaining 20% at the 16-bar fallback close. If a target is not reached, its quantity remains in the residual fallback leg.
- `partial-50-close-target-1p0-hold-16`: exit 50% of quantity at the first close-confirmed `+1.0 ATR`; close remaining 50% at the 16-bar fallback close.

These candidates are fixed, named, and not an optimizer. If none reaches realistic-cost `8/8`, the hypothesis is falsified for this slice.

A candidate may be early-falsified once a required quarter fails under realistic costs, because `8/8` is then impossible. Any remaining required quarters must stay visible in the scorecard as blocked/not run after early falsification and must not be counted as passes.

## Engine semantics
Extend `BacktestExitProfileConfig` with an optional `partial_targets` tuple/list of deterministic partial target legs. Each leg has:

- `quantity_fraction` with the profile total exactly summing to less than `1.0`, leaving residual quantity for fallback;
- `target_atr` using entry-time ATR;
- `trigger` as either `intrabar` or `close`.

When partial targets are configured:

1. Use only already accepted trades; do not affect level detection, scoring, gates, filters, sizing, or entry selection.
2. Read entry-time ATR from the existing feature snapshot. If ATR is unavailable or non-positive, close 100% at the configured maximum-hold close and record `missing_entry_atr_partial_fixed_holding_close`.
3. For each post-entry bar up to `fixed_holding_bars`, trigger each unfilled partial leg when its threshold is reached by `bar.high` for intrabar legs or `bar.close` for close-confirmed legs.
4. Same-bar target ordering is deterministic from lower ATR target to higher ATR target; if multiple legs share a threshold, keep declared order.
5. Any unfilled partial quantity plus the residual runner is closed at the fallback close.
6. Compute the aggregate trade as the sum of leg gross PnL, spread/slippage, notional commission, and funding using each leg quantity and holding bars. This keeps the existing single-trade report and scorecard contract while making partial exits cost-aware.
7. Serialize `exit_reason=partial_exit`, `exit_profile_partial_targets`, `exit_profile_partial_filled_legs`, `exit_profile_partial_fallback_fraction`, and settings in trade metadata and batch artifacts.

## No-lookahead boundary
Partial-exit profiles use entry-time ATR and post-entry bars only after the trade exists. They do not prefilter entries or use future labels before trade creation. Reference behavior without a selected partial-exit profile must remain unchanged.

## Verification
- Strict OpenSpec validation before source implementation.
- Targeted unit tests for partial profile validation, intrabar partial leg fill, close-confirmed partial leg fill, multiple target ordering, missing ATR fallback, aggregate cost/PnL accounting, and unchanged default/reference selection.
- Quarterly batch command pattern:
  `env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.crypto_batch --preset quarterly-2023-2024 --gate-profile <profile> --reuse-market-data --output-dir artifacts/partial-exit-profile-comparison/<profile> --market-data-dir artifacts/batch-market-data`
- Realistic-cost command pattern:
  `env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.crypto_batch --preset quarterly-2023-2024 --gate-profile <profile> --reuse-market-data --output-dir artifacts/partial-exit-profile-comparison-realistic/<profile> --market-data-dir artifacts/batch-market-data --spread 1.0 --slippage 0.5 --commission-per-unit 0.0 --funding-per-bar 0.0 --commission-rate 0.00055 --funding-rate-per-bar 0.00001`
- Project checks: targeted pytest, full pytest, ruff, pyright, OpenSpec validate all, `git diff --check`, duplicate spec/archive-name check.
