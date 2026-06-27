# Design

## Context

Reference before this change:

- profile: `conservative-v1-m15-slope-positive-max-trades-8`
- required windows: `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, `2024q4`
- configured thresholds: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, `require_no_feed_gaps=true`
- archived reference artifact: `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/2396740c76d50b91/summary.json`
- current reference score: `5/8`; failing quarters are `2024q1`, `2024q2`, `2024q4`
- realistic-cost success condition: `8/8` after `spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055` per side, and `funding_rate_per_bar=0.00001`

Pre-change quarterly scorecard:

| Quarter | Status | Key blockers | Net profit | Profit factor | Max drawdown | Artifact |
| --- | --- | --- | ---: | ---: | ---: | --- |
| 2023q1 | pass | none | 5614.00 | 1.1364 | -0.3157 | `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/2396740c76d50b91/summary.json` |
| 2023q2 | pass | none | 7018.80 | 1.1949 | -0.3471 | same |
| 2023q3 | pass | none | 4324.80 | 1.1820 | -0.1866 | same |
| 2023q4 | pass | none | 7203.20 | 1.1232 | -0.2635 | same |
| 2024q1 | fail | net_profit_below_threshold; profit_factor_below_threshold; max_drawdown_below_threshold | -6187.60 | 0.9542 | -1.1749 | same |
| 2024q2 | fail | net_profit_below_threshold; profit_factor_below_threshold; max_drawdown_below_threshold | -483.60 | 0.9957 | -0.7581 | same |
| 2024q3 | pass | none | 28130.00 | 1.2489 | -0.2225 | same |
| 2024q4 | fail | max_drawdown_below_threshold | 9230.40 | 1.0551 | -0.4225 | same |

Primary mechanism for this slice: the failed quarters have both favorable and adverse excursions in the path-risk diagnostics. Long holds and trailing exits increased drawdown, while the `0.01 ATR` stop was too cost-sensitive. The candidate set tests whether moderately tight asymmetric ATR stops can reduce drawdown without requiring the microscopic stop that failed realistic costs.

## Candidate set rationale

- `stop-0p25-target-2p0-hold-8`: closest bounded follow-up to the baseline-only tight stop, but wide enough to avoid a microscopic one-tick-like stop.
- `stop-0p5-target-2p0-hold-8`: tests a less noise-sensitive protective stop while keeping the same target and horizon.
- `stop-0p75-target-2p5-hold-16`: tests whether a wider stop plus larger target and longer cap can improve average trade while retaining drawdown control.

## Bounded scale-in guardrail

The optional averaging/scale-in branch is a separate research profile, not a default behavior change. It exists to test whether controlled entry-price improvement can move failed quarters toward `8/8` without breaking the drawdown threshold.

Required constraints:

- one fixed named profile only: `conservative-v1-m15-slope-positive-max-trades-8-bounded-scalein-1add-atr-stop-0p5-target-2p0-hold-8`;
- at most one additional entry per original accepted trade;
- fixed add size and fixed maximum total notional/exposure per trade;
- deterministic add trigger documented in artifacts before quarterly scoring;
- no recursive averaging, martingale multipliers, dynamic add count, or post-hoc tuning;
- realistic-cost scoring includes commission, spread, slippage, and funding impact from all added notional and extra turnover;
- unchanged success threshold: `8/8` quarters after realistic costs, with `min_max_drawdown=-0.35` still enforced.

If this profile increases net profit but causes any quarter to fail max drawdown, the result is falsified risk evidence, not partial success.

## Approach

1. Reuse `BacktestExitProfileConfig` fields `fixed_holding_bars`, `stop_atr`, and `target_atr`; no new exit engine semantics are needed.
2. Register exactly three fixed named profiles in the batch profile resolver.
3. Keep profile resolution scoped to explicit `--gate-profile` names; default/reference behavior remains unchanged.
4. If asymmetric ATR candidates remain below `8/8`, optionally register the one bounded scale-in profile behind its explicit profile name.
5. Run quarterly BTCUSDT public-data batches for each candidate using cached market data.
6. Run the realistic-cost robustness summarizer on candidate summaries.
7. Stop on a candidate only if realistic-cost scorecard is `8/8`; otherwise archive the measured result as falsified evidence and do not start a new hypothesis in this run.

## Risks

- Moderate ATR stops can still reduce winners too early or leave costs too high.
- The candidate set may worsen previously passed quarters; that is falsifying evidence, not a reason to lower thresholds.
- Because exit profiles do not change entry selection, realistic costs may remain impossible unless gross edge per trade improves substantially.
- Bounded scale-in can increase turnover and drawdown; any drawdown breach still fails the quarter even if profit improves.

## Verification

- Strict OpenSpec validation before source implementation.
- Targeted tests for named profile resolution and serialized settings.
- Quarterly batch command pattern:
  `env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.crypto_batch --preset quarterly-2023-2024 --gate-profile <profile> --reuse-market-data --output-dir artifacts/asymmetric-atr-exit-profile-comparison/<profile> --market-data-dir artifacts/batch-market-data`
- Realistic-cost summary command:
  `env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.realistic_cost_profile_search <summary> ... --output-dir artifacts/asymmetric-atr-exit-profile-comparison-summary/realistic-cost`
- Project checks: targeted pytest, full pytest, ruff, pyright, OpenSpec validate all, `git diff --check`, duplicate spec/archive-name check.
