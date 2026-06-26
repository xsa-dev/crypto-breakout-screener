## 1. OpenSpec readiness
- [x] 1.1 Confirm the repo is clean after `implement-breakout-context-feature-diagnostics` commit.
- [x] 1.2 Confirm this change is research filter comparison only and does not add production/live/private scope.
- [x] 1.3 Validate this change strictly and validate all OpenSpec specs before source edits.
- [x] 1.4 Stop for human GO before implementation.

## 2. Feature-filter configuration
- [x] 2.1 Add typed disabled-by-default feature-filter config separate from lifecycle research gates.
- [x] 2.2 Support M15 EMA slope positive requirement.
- [x] 2.3 Support H1 long trend requirement with explicit missing-context skip reason.
- [x] 2.4 Support candle body ratio cap.
- [x] 2.5 Serialize feature-filter settings in report parameters or batch summary.

## 3. Backtest engine behavior
- [x] 3.1 Evaluate feature filters only from no-lookahead entry feature snapshots.
- [x] 3.2 Apply feature filters after setup scoring and before trade creation.
- [x] 3.3 Preserve baseline and `conservative-v1` trade selection when feature filters are disabled.
- [x] 3.4 Record deterministic skip counters for feature-filter rejections.
- [x] 3.5 Ensure H1/H4/D1 context filters use closed context candles, not open-time candles that have not closed.

## 4. Batch profiles and reporting
- [x] 4.1 Add named profile `conservative-v1-m15-slope-positive`.
- [x] 4.2 Add named profile `conservative-v1-h1-long`.
- [x] 4.3 Add named profile `conservative-v1-m15-slope-positive-h1-long`.
- [x] 4.4 Add named profile `conservative-v1-m15-slope-positive-body-cap`.
- [x] 4.5 Keep `baseline` and `conservative-v1` behavior unchanged.
- [x] 4.6 Include feature-filter settings and skip counters in batch/report artifacts.

## 5. Research comparison
- [x] 5.1 Run or reuse public BTCUSDT quarterly data for baseline and conservative-v1 reference.
- [x] 5.2 Run BTCUSDT quarterly batches for each new named feature-filter profile.
- [x] 5.3 Compare profiles using existing hypothesis verdict thresholds.
- [x] 5.4 Report whether any profile improves passed-window count, max drawdown, profit factor, trade count, and net profit.
- [x] 5.5 State explicitly that successful filters are follow-up research evidence only, not production approval.

## 6. Tests
- [x] 6.1 Test default feature-filter config is disabled and preserves existing backtest behavior.
- [x] 6.2 Test M15 EMA slope positive filter passes/skips deterministically.
- [x] 6.3 Test H1 long filter passes/skips deterministically and treats missing context explicitly.
- [x] 6.4 Test candle body cap passes/skips deterministically.
- [x] 6.5 Test combined profile settings are serialized in batch summaries.
- [x] 6.6 Test no-lookahead context close-time alignment for H1 filter.
- [x] 6.7 Test no private env/API/secrets are read or emitted.

## 7. Verification
- [x] 7.1 Run targeted backtesting/reporting tests.
- [x] 7.2 Run crypto historical experiment tests.
- [x] 7.3 Run crypto batch tests.
- [x] 7.4 Run `uv run pytest`.
- [x] 7.5 Run `uv run ruff check .`.
- [x] 7.6 Run `uv run pyright`.
- [x] 7.7 Run `npx --yes @fission-ai/openspec@1.4.1 validate implement-breakout-rule-filter-comparison --strict --no-interactive`.
- [x] 7.8 Run `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`.
- [x] 7.9 Run `git diff --check`.
- [x] 7.10 Archive the OpenSpec change before commit boundary.
