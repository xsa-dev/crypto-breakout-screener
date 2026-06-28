# Design

## Restored hypothesis context

Current owner goal: find and verify a breakout research profile that reaches `8/8` quarterly windows (`2023q1..2024q4`) for a shared-bankroll multi-coin USDT portfolio. Success is measured on one combined USD/USDT equity curve, not independent per-symbol deposits, under realistic costs, fixed per-trade notional cap, fixed total exposure cap, no implicit leverage, configured max drawdown/profit factor/net profit thresholds, no feed gaps for promoted universe runs, and explicit regime segmentation.

Last archived altcoin-universe evidence did not promote past `2024q1`: fixed-50, `target-4p0-hold-32`, starting equity `10000`, max trade notional `1000`, max total open notional `3000`, realistic cost settings `spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055`, `funding_rate_per_bar=0.00001`, artifact `artifacts/altcoin-universe-portfolio-comparison-regime-smoke-reaggregated-ledger-fix/conservative-v1-m15-slope-positive-max-trades-8-target-4p0-hold-32/520b158e637db140/summary.json`. `2024q1` was blocked with net `-9799.606491774299`, PF `0.1283106575002619`, max DD `-0.979960649177431`, and `bull_long` PnL equal to the full accepted loss.

Primary blocker for this foundation change: `2024q1` accepted `bull_long` trades include candidates that are structurally cost-dominated under the configured absolute spread/slippage model and consume the shared bankroll before richer algorithmic decisions can help. This change tests one low-risk selection mechanism that can block such entries causally at entry time.

## Portfolio selection profile

Add a disabled-by-default portfolio selection profile named `cost-feasible-v1`. The default profile is `none` and preserves current behavior and existing artifacts unless explicitly selected.

The profile applies inside `crypto_portfolio_batch` after symbol-level backtests produce trade candidates and before exposure caps allocate shared bankroll. It uses only fields already present at entry time:

- entry price;
- trade notional before cap scaling;
- configured spread and slippage cost assumptions;
- configured commission and funding-rate assumptions;
- existing `regime_decision`.

The fixed rule is deliberately simple and deterministic:

- estimate one-unit round-trip friction as `spread + 2 * slippage_per_unit`;
- estimate relative friction as `round_trip_friction / entry_price`;
- block long-enabled entries when `relative_friction > max_round_trip_friction_ratio`;
- default `max_round_trip_friction_ratio = 0.02` for `cost-feasible-v1`.

Rationale: with the current configured stress costs, entries where price is too close to the absolute friction assumption are not plausible long-breakout portfolio allocations. Blocking them is a selection/risk-control decision, not a cost-model change. The skipped trades remain in the portfolio trade ledger with blocker `portfolio_selection_cost_feasibility` and count as skipped/blocked signals.

The rule must fail closed for missing or non-positive prices by blocking as `portfolio_selection_missing_price`, not by accepting the trade.

## Reporting

Portfolio summary JSON and scorecard artifacts SHALL include:

- `selection_profile`;
- `selection_settings`;
- `selection_skip_counts`;
- unchanged cost model settings;
- unchanged thresholds;
- one row per quarter with status, blockers, trade counts, accepted counts, skipped counts, net profit, profit factor, max drawdown, threshold buffers, symbol count, blocked symbol count, and artifact paths.

Portfolio trade CSV SHALL preserve skipped rows with their blocker, regime label, decision, source trade id, and source artifact dir.

Per-regime contribution SHALL include skipped/blocked selection signals inside `skipped_blocked_signal_count`, so `bull_long` reports both accepted trades and cost-feasibility skips.

## Experiment path

1. Implement and test the opt-in profile.
2. Run `2024q1` smoke on the fixed-50 universe with the same baseline profile and realistic costs:
   `env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.crypto_portfolio_batch --windows '2024q1:2024-01-01T00:00:00Z/2024-04-01T00:00:00Z' --universe fixed-50-altcoins --starting-equity 10000 --max-trade-notional 1000 --max-total-open-notional 3000 --spread 1.0 --slippage 0.5 --commission-rate 0.00055 --funding-rate-per-bar 0.00001 --selection-profile cost-feasible-v1 --gate-profile conservative-v1-m15-slope-positive-max-trades-8-target-4p0-hold-32 --market-data-dir artifacts/batch-market-data --output-dir artifacts/cost-feasible-portfolio-selection-smoke --reuse-market-data --max-workers 8`
3. If smoke has no technical blockers and materially improves the primary blockers, run promoted `quarterly-2023-2024` on the same fixed-50 universe and record full scorecard/regime evidence.
4. If smoke is technically blocked by missing public data, record the blocker and do not claim falsified economics for the unavailable quarters.
5. If promoted full-universe scorecard completes below `8/8`, archive as falsified/negative evidence.

## Relationship to algorithmic follow-ups

This change is intentionally narrow. It should land before, or be reused by, the stronger algorithmic changes:

- quarter diagnostics;
- lifecycle/state audit;
- algorithmic score;
- top-N shared-bankroll selection;
- retest/confirmation behavior;
- fast-failure exit.

Those changes must not be claimed as complete by this cost-feasibility foundation.

## Risks and constraints

- A cost-feasibility gate can over-block low-price symbols and produce no trades. That is a failed hypothesis unless all required thresholds still pass with at least one trade per quarter.
- Missing data remains a technical blocker for promoted universe runs; this change does not permit dropping symbols from the approved fixed-50 universe.
- The selection rule must not inspect realized PnL, exit price, future bars, per-symbol outcomes, or archived contribution rankings.
- This does not implement shorts. `bear_short_or_avoid` remains risk-off/blocked evidence.
