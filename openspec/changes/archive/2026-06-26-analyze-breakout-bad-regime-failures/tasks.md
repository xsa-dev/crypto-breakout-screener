## 1. OpenSpec readiness
- [x] 1.1 Confirm the previous drawdown-regime-controls change is archived and committed.
- [x] 1.2 Confirm this change is diagnostic-only and does not approve production trading.
- [x] 1.3 Validate OpenSpec strictly before implementation.

## 2. Diagnostic implementation
- [x] 2.1 Add deterministic failed-window diagnostics for the fixed profile `conservative-v1-m15-slope-positive-max-trades-8`.
- [x] 2.2 Export worst drawdown run attribution for failed windows.
- [x] 2.3 Export bad-regime bucket summaries using existing no-lookahead entry/context features where available.
- [x] 2.4 Include profile/window/run identifiers in every diagnostic artifact.
- [x] 2.5 Keep default backtest behavior unchanged.

## 3. Tests
- [x] 3.1 Test diagnostic artifact schema and stable ordering.
- [x] 3.2 Test aggregation math for trade count, net PnL, drawdown/adverse-run fields, and bucket grouping.
- [x] 3.3 Test failed-window filtering targets only blocked/failed windows.
- [x] 3.4 Test candidate regime buckets use entry-time fields rather than future outcomes.
- [x] 3.5 Test no private credentials or `.env` values are read or serialized.

## 4. Real research run
- [x] 4.1 Run quarterly 2023-2024 BTCUSDT public-data batch for `conservative-v1-m15-slope-positive-max-trades-8` with diagnostics enabled.
- [x] 4.2 Inspect diagnostics for 2024q1, 2024q2, and 2024q4.
- [x] 4.3 Report whether losses cluster by days, drawdown runs, or feature buckets.
- [x] 4.4 State the next candidate hypothesis without implementing it in this change unless separately approved.

## 5. Verification and archive
- [x] 5.1 Run targeted tests.
- [x] 5.2 Run full `uv run pytest`.
- [x] 5.3 Run `uv run ruff check .`.
- [x] 5.4 Run `uv run pyright`.
- [x] 5.5 Run strict OpenSpec validation for this change and all specs.
- [x] 5.6 Run `git diff --check`.
- [x] 5.7 Archive the OpenSpec change.
- [x] 5.8 Run final validation after archive.
- [x] 5.9 Final critical review before commit.
