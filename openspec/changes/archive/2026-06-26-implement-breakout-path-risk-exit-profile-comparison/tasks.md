## 1. OpenSpec readiness
- [x] 1.1 Continue the active OpenSpec change `implement-breakout-path-risk-exit-profile-comparison`; the previous path-risk diagnostic evidence is archived and the current reference remains 5/8.
- [x] 1.2 Record the pre-implementation 5/8 quarterly scorecard with failed-window blockers and artifact path in `proposal.md`.
- [x] 1.3 Validate this OpenSpec change strictly before source-code implementation.

## 2. Implementation
- [x] 2.1 Add disabled-by-default `BacktestExitProfileConfig` preserving default/reference one-bar close behavior.
- [x] 2.2 Implement fixed-holding exit semantics after entry without changing entry selection.
- [x] 2.3 Implement fixed ATR stop/target exit semantics with conservative same-bar stop-first ordering.
- [x] 2.4 Add named batch profiles for the fixed comparison set.
- [x] 2.5 Add batch CSV/JSON fields for exit profile name, settings, and counters.
- [x] 2.6 Keep gate, feature, risk, regime, confirmation, and exit profile reporting separate.

## 3. Tests
- [x] 3.1 Add unit tests proving default exit behavior is unchanged.
- [x] 3.2 Add unit tests for fixed hold-2/hold-4 exit timing and holding bars.
- [x] 3.3 Add unit tests for ATR stop, ATR target, no-threshold-hit max-hold, missing ATR fallback, and same-bar stop-first ordering.
- [x] 3.4 Add batch tests for named profile resolution and CSV/JSON serialization fields.
- [x] 3.5 Add no-lookahead tests proving exit profiles do not alter trade entry timestamps/counts before exit logic is applied.

## 4. Quarterly experiment loop
- [x] 4.1 Reuse the archived reference artifact `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/2396740c76d50b91/path-risk-window-summary.csv` to confirm the 5/8 baseline.
- [x] 4.2 Run quarterly 2023-2024 public BTCUSDT batch for each fixed exit profile.
- [x] 4.3 Parse and record scorecard for every profile: pass/fail quarters, blockers, trade count, net profit, worst max drawdown, profit factor, artifact paths.
- [x] 4.4 If a profile reaches 8/8, stop further experimentation and proceed to final validation/archive/commit/success notification. Final successful profile: `conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p01-target-2p0`, summary `artifacts/exit-profile-comparison/crypto/BTCUSDT/f7f80591545417ed/summary.json`, 8/8 passed.
- [x] 4.5 Initial fixed profiles did not improve toward 8/8: hold-2 = 1/8, hold-4 = 0/8, ATR stop 1.0/target 1.5/max-hold 4 = 1/8 plus rerun evidence for the file-conflicted 2023q1 window, ATR stop 1.5/target 2.0/max-hold 8 = 2/8 plus rerun evidence for the file-conflicted 2023q2 window. Leave the change unfinished; do not archive/commit until a narrower in-scope profile or separate follow-up reaches 8/8.
- [x] 4.6 Test the single tight protective-stop candidate `conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p01-target-2p0` over the full quarterly scorecard; this is still exit-only and does not change entry/no-trade filters or thresholds. Result: 2023q1..2024q4 all passed with unchanged configured research thresholds.

## 5. Final validation and closure
- [x] 5.1 Interim validation passed: `uv run pytest`, `uv run ruff check .`, `uv run pyright`, strict OpenSpec validation, all-spec validation, and `git diff --check`.
- [x] 5.2 Perform self-review for scope, no-lookahead, threshold preservation, secret safety, and artifact completeness. Review: exit-only path-risk profile, no entry/no-trade/regime/confirmation filter broadening, no private API/live/production approval, artifacts recorded, thresholds unchanged.
- [x] 5.3 Update tasks with final evidence.
- [x] 5.4 Archive only if the quarterly scorecard reaches 8/8 or an honest external blocker prevents further local evaluation. Archive after final validation is allowed because the final scorecard is 8/8.
- [x] 5.5 Commit only scoped files if archived and repository state is safe.
