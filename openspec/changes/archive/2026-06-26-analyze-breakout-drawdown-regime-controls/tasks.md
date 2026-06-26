## 1. OpenSpec readiness
- [x] 1.1 Confirm repo is clean after `implement-breakout-rule-filter-comparison` commit.
- [x] 1.2 Confirm this change is drawdown/regime risk-control research only.
- [x] 1.3 Confirm no ML, optimization search, live/private API, UI, FX, ETH/top-N, or production approval scope is included.
- [x] 1.4 Validate this OpenSpec change in strict mode before source edits.

## 2. Implementation
- [x] 2.1 Add or extend disabled-by-default research risk-control settings without changing baseline/conservative/default behavior.
- [x] 2.2 Add named profiles for stricter daily stop loss, lower max trades/day, and longer loss cooldown on top of `conservative-v1-m15-slope-positive`.
- [x] 2.3 Optional two-loss-day-pause profile intentionally not implemented in this slice; required profiles remained fixed and small.
- [x] 2.4 Record risk-control settings and skip/pause counts in batch summary CSV/JSON.
- [x] 2.5 Keep heavy feature/trade data in existing artifacts; avoid bloating summary JSON.
- [x] 2.6 Preserve public BTCUSDT M15 + H1/H4/D1 context-only research boundary.

## 3. Tests
- [x] 3.1 Test default risk controls are disabled and preserve existing trade selection/metrics.
- [x] 3.2 Test stricter daily stop profile settings serialize and gate entries only after realized exit-day losses.
- [x] 3.3 Test max-trades/day profile uses UTC entry day and records deterministic skip counts.
- [x] 3.4 Test longer cooldown-after-loss profile uses realized losing trade exits and records deterministic skip counts.
- [x] 3.5 Optional two-loss-day-pause tests not needed because the optional profile was intentionally not implemented.
- [x] 3.6 Test cross-midnight realized loss attribution remains exit-day based.
- [x] 3.7 Test batch summaries include profile/settings/skip counts and worst-day artifact references.

## 4. Verification
- [x] 4.1 Run targeted pytest for backtesting and crypto batch tests.
- [x] 4.2 Run full `uv run pytest`.
- [x] 4.3 Run `uv run ruff check .`.
- [x] 4.4 Run `uv run pyright`.
- [x] 4.5 Run OpenSpec strict validation for this change and all specs.
- [x] 4.6 Run `git diff --check`.

## 5. Experiments
- [x] 5.1 Run quarterly 2023-2024 reference profile `conservative-v1-m15-slope-positive` or reuse committed artifact paths if unchanged.
- [x] 5.2 Run quarterly profiles for daily stop 3000, daily stop 2000, max trades/day 8, and loss cooldown 12.
- [x] 5.3 Optional two-loss-day-pause experiment not run because the optional profile was intentionally not implemented.
- [x] 5.4 Compare trade count, net profit, worst max drawdown, profit factor, passed-window count, blockers, and worst-day summaries.
- [x] 5.5 Report whether any profile supports the hypothesis; if not, identify remaining failed windows and blockers.

## 6. Archive and commit readiness
- [x] 6.1 Update tasks to complete only after verified evidence exists.
- [x] 6.2 Archive OpenSpec change after verification.
- [x] 6.3 Run final verification after archive.
- [x] 6.4 Perform final critical review before commit.
- [x] 6.5 Commit only after review is GO.
