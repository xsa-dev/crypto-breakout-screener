# Design

## Baseline
Use the fixed current best profile as the primary reference:

`conservative-v1-m15-slope-positive-max-trades-8`

Reference evidence from the archived bad-regime diagnostic run:

- batch_id: `bb49e97621f8e79c`
- trades: 4176
- net: 54850.00
- worst max drawdown: -1.1749
- passed: 5/8
- failed: 3/8
- hypothesis_supported: false

Remaining failed windows:

- `2024q1`: negative expectancy and drawdown blocked
- `2024q2`: near-flat/negative expectancy and drawdown blocked
- `2024q4`: profitable overall, drawdown blocked

## Candidate profile set
Compare only this fixed set; do not add unreviewed thresholds during implementation.

Required profiles:

1. `conservative-v1-m15-slope-positive-max-trades-8`
   - reference profile

2. `conservative-v1-m15-slope-positive-max-trades-8-atr25-block`
   - base profile plus skip entries where `feature_atr_percentile <= 0.25`
   - rationale: low ATR percentile was negative in all remaining failed windows

3. `conservative-v1-m15-slope-positive-max-trades-8-atr25-breakout1-block`
   - profile 2 plus skip entries where `feature_breakout_distance_atr > 1.0`
   - rationale: `2024q1` losses were heavily concentrated in breakout distance `> 1.0 ATR`

4. `conservative-v1-m15-slope-positive-max-trades-8-atr25-body75-block`
   - profile 2 plus skip entries where `feature_candle_body_range_ratio > 0.75`
   - rationale: `2024q4` drawdown was concentrated in large candle-body buckets

Optional profile only if implementation remains small and required profiles are complete:

5. `conservative-v1-m15-slope-positive-max-trades-8-atr25-body25-75-block`
   - profile 2 plus skip entries where `feature_candle_body_range_ratio <= 0.25` or `> 0.75`
   - rationale: `2024q2` small body bucket and `2024q4` large body bucket were both negative

## Implementation approach
Prefer extending `BacktestFeatureFilterConfig` with deterministic entry-time conditions rather than introducing a new engine subsystem:

- `min_atr_percentile: float | None`
- `max_breakout_distance_atr: float | None`
- `max_candle_body_range_ratio: float | None`
- optional `min_candle_body_range_ratio: float | None` only if optional profile is implemented

The engine already computes feature snapshots before trade creation. New filter checks SHALL use those same entry-time snapshot values.

## Reporting
Keep existing fields and add clear regime-filter auditability without conflating it with lifecycle/risk controls:

- `regime_filter_profile`
- `regime_filter_settings_json`
- `regime_filter_skip_counts_json`

If implementation reuses `feature_filter_profile` internally, summary output must still expose the regime-filter name/settings distinctly so the experiment can be audited.

Skip reasons SHOULD be deterministic and specific, e.g.:

- `skipped_feature_atr_percentile_below_min`
- `skipped_feature_breakout_distance_atr_above_cap`
- `skipped_feature_candle_body_ratio_above_cap`
- `skipped_feature_candle_body_ratio_below_min`

## Acceptance interpretation
The hypothesis is supported only if the final aggregate reports:

- `technical_pass=true`
- `hypothesis_supported=true`
- all 8 quarterly windows pass the configured research thresholds

If the best new profile improves pass count/drawdown but still has blocked windows, report the hypothesis as improved but not supported.

## Data and no-lookahead boundaries
- Use only existing public OHLCV/context data and already computed entry-time feature snapshots.
- H1/H4/D1 context remains usable only after context candle close time.
- Do not use future PnL, future drawdown, future labels, or the candidate trade outcome to decide entry.
- Do not introduce order book / стакан / L2 / DOM / trade tape / taker-flow data in this change.

## Verification plan
- Unit tests for each new filter reason and combined behavior.
- Batch summary serialization tests for profile/settings/skip counts.
- Full verification: `uv run pytest`, `uv run ruff check .`, `uv run pyright`, OpenSpec validation, and `git diff --check`.
- Real quarterly 2023-2024 runs for all required profiles using `artifacts/feature-diagnostics-market-data`.
- Parse summary CSV/JSON and compare passed windows, net, worst drawdown, profit factor, blockers, and skip counts.
