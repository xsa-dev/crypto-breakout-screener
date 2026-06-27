# Design

## Fixed hypothesis target
Reference before this change:

- profile: `conservative-v1-m15-slope-positive-max-trades-8`
- required windows: `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, `2024q4`
- configured thresholds: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, `require_no_feed_gaps=true`
- archived reference artifact: `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/2396740c76d50b91/summary.json`
- current reference score: `5/8`; failing quarters are `2024q1`, `2024q2`, `2024q4`
- realistic-cost success condition: `8/8` after `spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055` per side, and `funding_rate_per_bar=0.00001`

## Hypothesis and mechanism
The selected mechanism is deterministic partial profit capture with residual-only protection after entry. Previous partial exits left the residual fallback runner unprotected, while previous break-even/trailing profiles protected the whole position and did not bank partial profits first. This slice tests whether banking a fixed partial leg and then protecting only the residual runner can reduce drawdown in failed windows while preserving enough continuation upside to survive realistic costs.

## Candidate set
- `partial-50-target-1p0-residual-breakeven-hold-16`: exit 50% at intrabar `entry_price + 1.0 * entry_time_ATR`; after that leg fills, close the remaining 50% at entry price if a later bar touches entry, otherwise close at the 16-bar fallback close.
- `partial-30-50-targets-1p0-2p0-residual-breakeven-hold-16`: exit 30% at intrabar `+1.0 ATR`, 50% at intrabar `+2.0 ATR`; after at least one leg fills, close any remaining fallback runner at entry price on a later touch, otherwise close at the 16-bar fallback close.
- `partial-50-target-1p0-residual-trail-1p0-giveback-1p0-hold-16`: exit 50% at intrabar `+1.0 ATR`; after that leg fills, track subsequent highs for the residual runner and close the residual on a `1.0 ATR` giveback from the best post-activation high, otherwise close at the 16-bar fallback close.

These candidates are fixed, named, and not an optimizer. If none reaches realistic-cost `8/8`, the hypothesis is falsified for this slice.

## Execution semantics
1. Use only already accepted trades; do not affect level detection, scoring, gates, filters, sizing, or entry selection.
2. Read entry-time ATR from the existing feature snapshot. If ATR is unavailable or non-positive, close 100% at the configured maximum-hold close and record `missing_entry_atr_partial_fixed_holding_close`.
3. For each post-entry bar up to `fixed_holding_bars`, trigger each unfilled partial leg when its threshold is reached by `bar.high`.
4. Same-bar partial target ordering is deterministic from lower ATR target to higher ATR target; if multiple legs share a threshold, keep declared order.
5. Residual protection is inactive until at least one partial leg has filled. It may act on the same bar only after the partial target ordering has filled the leg, using conservative same-bar ordering for residual protection checks.
6. Residual break-even closes only the current unfilled fallback fraction at raw entry price when a post-activation bar touches entry price.
7. Residual trailing starts from the high observed at/after activation and closes only the current unfilled fallback fraction at `trailing_high - trailing_giveback_atr * entry_time_ATR` when touched.
8. Any unfilled partial quantity plus residual runner that is not protected earlier is closed at the fallback close.
9. Compute the aggregate trade as the sum of leg gross PnL, spread/slippage, notional commission, and funding using each leg quantity and holding bars.
10. Serialize `exit_reason=partial_exit`, `exit_profile_partial_targets`, `exit_profile_partial_filled_legs`, `exit_profile_partial_fallback_fraction`, `exit_profile_residual_protection`, and settings in trade metadata and batch artifacts.

## Verification
- Strict OpenSpec validation before source implementation.
- Targeted unit tests for residual break-even activation after partial target, residual trailing giveback after partial target, inactive protection before a partial fill, missing ATR fallback, validation, and named profile serialization.
- Quarterly batch command pattern:
  `env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.crypto_batch --preset quarterly-2023-2024 --gate-profile <profile> --reuse-market-data --output-dir artifacts/protected-partial-exit-profile-comparison/<profile> --market-data-dir artifacts/batch-market-data`
- Realistic-cost classification command pattern using the project robustness helper over completed candidate `summary.json` files, or early-falsified single-window evidence when a required realistic quarter fails.
- Full gates: pytest, ruff, pyright, strict OpenSpec validation, `git diff --check`, duplicate spec/archive-name check.

## Safety and boundaries
- No private/live API, account data, broker execution, production approval, push, MR, merge, or Telegram success unless realistic-cost `8/8` is achieved after archive/commit.
- No threshold weakening, missing-quarter pass credit, entry filter changes, volatility/regime filters, confirmation filters, order book/DOM/L2/taker-flow, ML, martingale, or averaging.
