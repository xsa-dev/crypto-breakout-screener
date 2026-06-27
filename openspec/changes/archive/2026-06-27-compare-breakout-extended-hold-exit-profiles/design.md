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

Primary mechanism for this slice: longer causal holding may skip some same-direction churn while allowing larger favorable excursions in `2024q1` and `2024q4`. `2024q2` is the primary risk because archived forward-path diagnostics showed weaker longer-horizon continuation there; this change must treat a `2024q2` miss as falsifying evidence rather than widening scope.

## Approach

1. Reuse `BacktestExitProfileConfig.fixed_holding_bars` and existing `_resolve_exit` fixed-holding behavior.
2. Register exactly three fixed named exit profiles: hold 8, 16, and 32 M15 bars.
3. Keep profile resolution scoped to explicit `--gate-profile` names; default/reference behavior remains unchanged.
4. Run quarterly BTCUSDT public-data batches for each candidate using cached market data.
5. Run the realistic-cost robustness summarizer on candidate summaries.
6. Stop on the first candidate only if realistic-cost scorecard is `8/8`; otherwise archive the best measured result as falsified evidence.

## Candidate set rationale

- `hold-8`: already suggested by path-risk horizon diagnostics and shorter than prior trailing profiles' max hold.
- `hold-16`: path-risk/forward-path diagnostics showed stronger `2024q1` and `2024q4` continuation at 16 bars, and longer open positions can lower turnover by skipping overlapping entries.
- `hold-32`: tests whether the same mechanism needs a full-session style hold while remaining a single fixed candidate, not a broad optimization.

## Risks

- Longer holding can worsen drawdown or turn winning baseline quarters into failing quarters.
- Funding stress grows with holding bars, so realistic-cost results may remain below `8/8` even if baseline improves.
- The slice intentionally does not add entry/no-trade filters; if `2024q2` remains adverse, the correct outcome is falsified evidence and closure.

## Verification

- Strict OpenSpec validation before source implementation.
- Targeted tests for named profile resolution and serialized settings.
- Quarterly batch command pattern:
  `env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.crypto_batch --preset quarterly-2023-2024 --gate-profile <profile> --output-dir artifacts/extended-hold-exit-profile-comparison/<profile> --market-data-dir artifacts/batch-market-data`
- Realistic-cost summary command:
  `env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.realistic_cost_profile_search <summary> ... --output-dir artifacts/extended-hold-exit-profile-comparison-summary/realistic-cost`
- Project checks: targeted pytest, full pytest, ruff, pyright, OpenSpec validate all, `git diff --check`, duplicate spec/archive-name check.
