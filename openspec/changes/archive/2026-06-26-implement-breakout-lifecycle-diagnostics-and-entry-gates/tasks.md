## 1. OpenSpec readiness
- [x] 1.1 Confirm the starting repository is clean after the batch runner commit.
- [x] 1.2 Confirm scope is lifecycle diagnostics plus configurable research entry gates only.
- [x] 1.3 Confirm out-of-scope items: live trading, private API, ETH/top-N, optimization search, production OOS approval, UI, full position simulator rewrite, and HTF strategy filter implementation.
- [x] 1.4 Validate this change strictly and validate all OpenSpec specs before source edits.

## 2. Lifecycle diagnostics
- [x] 2.1 Add deterministic daily summary export for completed backtest reports.
- [x] 2.2 Add deterministic weekly summary export for completed backtest reports.
- [x] 2.3 Add lifecycle diagnostics export with holding distribution, immediate re-entry counts/ratio, trades per bar, daily trade extremes, loss streaks, and side distribution.
- [x] 2.4 Add score-bucket PnL diagnostics.
- [x] 2.5 Include new artifact paths in exported report artifact paths.
- [x] 2.6 Preserve existing artifact schemas unless deliberately extended and tested.

## 3. Research entry gates
- [x] 3.1 Add a disabled-by-default research gate config to `BacktestConfig` or an equivalent nested model.
- [x] 3.2 Implement `min_entry_score` gate.
- [x] 3.3 Implement `cooldown_bars_after_trade` gate.
- [x] 3.4 Implement `cooldown_bars_after_loss` gate.
- [x] 3.5 Implement `block_immediate_reentry` gate.
- [x] 3.6 Implement `max_trades_per_day` gate.
- [x] 3.7 Implement `daily_stop_loss` gate.
- [x] 3.8 Record gate settings in parameter snapshots/config hash.
- [x] 3.9 Record skipped/rejected gate counts in diagnostics or unavailable reasons.

## 4. Batch comparison
- [x] 4.1 Add CLI/config support to run the crypto batch with a conservative gate profile or explicit gate options.
- [x] 4.2 Ensure batch summary records profile/gate settings or references the config hash/parameters sufficient to audit them.
- [x] 4.3 Repeat BTCUSDT quarterly batch for baseline and conservative gated profile.
- [x] 4.4 Report before/after trade count, max drawdown, net profit, PF, and hypothesis verdict.

## 5. Tests
- [x] 5.1 Test daily and weekly grouping with deterministic synthetic trades.
- [x] 5.2 Test immediate re-entry diagnostics on one-bar consecutive trades.
- [x] 5.3 Test holding distribution and score-bucket PnL diagnostics.
- [x] 5.4 Test default research gates are no-op relative to current fixture behavior.
- [x] 5.5 Test each gate type with deterministic fixture bars.
- [x] 5.6 Test batch summary includes gate/profile metadata.
- [x] 5.7 Test no private env/API/secrets are read or emitted.

## 6. Verification
- [x] 6.1 Run targeted lifecycle diagnostics/gates tests.
- [x] 6.2 Run crypto historical experiment tests.
- [x] 6.3 Run crypto batch tests.
- [x] 6.4 Run `uv run pytest`.
- [x] 6.5 Run `uv run ruff check .`.
- [x] 6.6 Run `uv run pyright`.
- [x] 6.7 Run `npx --yes @fission-ai/openspec@1.4.1 validate implement-breakout-lifecycle-diagnostics-and-entry-gates --strict --no-interactive`.
- [x] 6.8 Run `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`.
- [x] 6.9 Run `git diff --check`.
- [x] 6.10 Archive the OpenSpec change before commit boundary.
