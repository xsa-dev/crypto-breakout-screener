## 1. OpenSpec readiness
- [x] 1.1 Confirm repository is clean after lifecycle diagnostics commit.
- [x] 1.2 Confirm this change is diagnostics/features only and does not add ML training or new trade-selection filters.
- [x] 1.3 Confirm out-of-scope items: live trading, private API, ETH/top-N, optimization search, production OOS approval, UI, ML model training, new dependencies unless already present, and full position simulator rewrite.
- [x] 1.4 Validate this change strictly and validate all OpenSpec specs before source edits.

## 2. Feature extraction
- [x] 2.1 Add deterministic entry-time feature snapshot data structures or helpers.
- [x] 2.2 Include existing setup/scoring feature values where available.
- [x] 2.3 Add M15 technical features: ATR regime, candle body/range, close-position, breakout distance, EMA distance/slope, compression/range proxy, volume ratio.
- [x] 2.4 Add lifecycle state features known before entry: trades today, realized PnL today, bars since previous exit, previous loss flag, gate profile/settings metadata.
- [x] 2.5 Add optional H1/H4/D1 context feature extraction aligned to closed context bars at or before entry time.
- [x] 2.6 Mark unavailable context features explicitly without failing M15-only backtests.
- [x] 2.7 Ensure feature calculation never reads future bars, trade outcomes, or post-entry state.

## 3. Report artifacts
- [x] 3.1 Export `<run_id>-entry-feature-snapshots.csv`.
- [x] 3.2 Export `<run_id>-feature-bucket-pnl.csv`.
- [x] 3.3 Export `<run_id>-regime-bucket-summary.csv`.
- [x] 3.4 Export `<run_id>-worst-day-attribution.csv`.
- [x] 3.5 Add new artifact paths to exported report artifact paths.
- [x] 3.6 Preserve existing report artifact schemas unless deliberately extended and tested.

## 4. Crypto experiment and batch wiring
- [x] 4.1 Allow the crypto experiment runner to supply context CSV paths to feature diagnostics without changing default M15 execution behavior.
- [x] 4.2 Ensure manifests and summaries continue to record M15 execution plus H1/H4/D1 context datasets.
- [x] 4.3 Ensure batch summaries include feature-diagnostics artifact availability or references sufficient to audit them.
- [x] 4.4 Repeat BTCUSDT quarterly comparison for baseline and conservative-v1 with feature diagnostics.
- [x] 4.5 Report candidate feature/regime findings and explicitly state whether they are only follow-up hypotheses.

## 5. Tests
- [x] 5.1 Test entry feature snapshots are deterministic for the same report inputs.
- [x] 5.2 Test no-lookahead alignment for M15 features.
- [x] 5.3 Test H1/H4/D1 context alignment uses closed bars at or before entry time.
- [x] 5.4 Test missing context paths produce unavailable markers rather than failures.
- [x] 5.5 Test feature-bucket PnL, regime summaries, and worst-day attribution on deterministic synthetic trades.
- [x] 5.6 Test crypto experiment/batch artifact lists include feature diagnostics.
- [x] 5.7 Test no private env/API/secrets are read or emitted.

## 6. Verification
- [x] 6.1 Run targeted feature diagnostics tests.
- [x] 6.2 Run crypto historical experiment tests.
- [x] 6.3 Run crypto batch tests.
- [x] 6.4 Run `uv run pytest`.
- [x] 6.5 Run `uv run ruff check .`.
- [x] 6.6 Run `uv run pyright`.
- [x] 6.7 Run `npx --yes @fission-ai/openspec@1.4.1 validate implement-breakout-context-feature-diagnostics --strict --no-interactive`.
- [x] 6.8 Run `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`.
- [x] 6.9 Run `git diff --check`.
- [x] 6.10 Archive the OpenSpec change before commit boundary.
