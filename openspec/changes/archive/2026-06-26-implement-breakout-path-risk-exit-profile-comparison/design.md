# Design

## Fixed hypothesis target

Target profile before this change: `conservative-v1-m15-slope-positive-max-trades-8`.

Required quarterly windows:

- `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, `2024q4`.

Current reference scorecard is 5/8 with failures in `2024q1`, `2024q2`, and `2024q4`.

## Exit profile model

Add a disabled-by-default `BacktestExitProfileConfig` to the backtest config. Default config SHALL preserve existing one-bar close behavior exactly.

Named research profiles are resolved by the BTCUSDT batch runner from `gate_profile` names and recorded separately from other profile dimensions. Initial fixed profiles:

- `conservative-v1-m15-slope-positive-max-trades-8-hold-2`: close after 2 M15 bars unless insufficient future bars force the last available evaluated bar.
- `conservative-v1-m15-slope-positive-max-trades-8-hold-4`: close after 4 M15 bars unless insufficient future bars force the last available evaluated bar.
- `conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p01-target-2p0`: after entry, use entry-time ATR with a 0.01 ATR adverse stop and 2.0 ATR favorable target over the existing 1-bar lifecycle.
- `conservative-v1-m15-slope-positive-max-trades-8-atr-stop-1p0-target-1p5`: after entry, use entry-time ATR with a 1.0 ATR adverse stop and 1.5 ATR favorable target over a 4-bar maximum hold.
- `conservative-v1-m15-slope-positive-max-trades-8-atr-stop-1p5-target-2p0`: after entry, use entry-time ATR with a 1.5 ATR adverse stop and 2.0 ATR favorable target over an 8-bar maximum hold.

These are fixed profiles, not an optimizer. They are chosen from the diagnostic grid already used by path-risk analysis and target the shared failure mechanism: path-risk / exit / holding behavior after a valid entry.
The 0.01 ATR stop profile is a single tight protective-stop candidate added after the initial fixed profiles failed to improve beyond 2/8; it keeps the original one-bar holding lifecycle and tests whether adverse excursion containment, rather than longer holding, is the missing path-risk mechanism.

## OHLCV execution semantics

The engine remains closed-bar deterministic. Entry stays at the current breakout/confirmation close using the existing cost model.

For fixed-hold profiles:

- exit at the close of the configured future bar offset;
- if the future bar is unavailable near the end of a window, exit at the last available post-entry bar and record a counter/reason.

For ATR stop/target profiles:

- entry-time ATR is read from the existing entry feature snapshot (`feature_atr`);
- if ATR is unavailable, fall back to the fixed maximum-hold close and record `missing_entry_atr`;
- thresholds are evaluated only after the trade exists over bars `index+1..index+max_holding_bars`;
- for long-only current research, adverse stop is `entry_price - stop_atr * ATR`; favorable target is `entry_price + target_atr * ATR`;
- if both stop and target are touched in the same bar, use conservative deterministic ordering: stop first;
- otherwise exit at first touched threshold, or at max-hold close if neither threshold is reached;
- costs/commission/funding are computed for the actual holding bars, and slippage/spread semantics remain consistent with existing entry/exit cost modeling.

## No-lookahead boundary

Exit profiles may inspect post-entry bars only after a trade entry is already accepted. They SHALL NOT be visible to level detection, setup scoring, research gates, feature filters, confirmation filters, risk sizing, or entry selection.

## Reporting

Batch summaries add:

- `exit_profile`;
- `exit_profile_settings_json`;
- `exit_profile_counts_json`.

Per-trade metadata may include exit profile labels/counters, but existing report metric names stay unchanged. Batch verdict logic remains the configured threshold logic.

## Verification

Run before any archive/commit:

```bash
npx --yes @fission-ai/openspec@1.4.1 validate implement-breakout-path-risk-exit-profile-comparison --strict --no-interactive
npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive
uv run pytest
uv run ruff check .
uv run pyright
git diff --check
```

Real research batches:

```bash
uv run python -m src.app.breakout.experiments.crypto_batch --preset quarterly-2023-2024 --gate-profile <profile> --output-dir artifacts/exit-profile-comparison --market-data-dir artifacts/batch-market-data
```

For each profile, record passed/failed quarters, blockers, trade count, net profit, max drawdown, profit factor, artifact paths, and whether the score moved toward 8/8.
