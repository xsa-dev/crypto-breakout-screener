## 1. OpenSpec readiness
- [x] 1.1 Confirm no active OpenSpec changes and record unrelated dirty files.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 list` showed no active changes; `git status --short --branch` showed unrelated modified `.dev/autonomous_dev.sh`.
- [x] 1.2 Reconstruct the current reference scorecard and failing windows before implementation.
  - Evidence: proposal records `conservative-v1-m15-slope-positive-max-trades-8` as `5/8` with failed quarters `2024q1`, `2024q2`, `2024q4` from `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/2396740c76d50b91/summary.json`.
- [x] 1.3 Validate this change strictly before source implementation.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 validate compare-breakout-equity-drawdown-guard-profiles --strict --no-interactive` and `validate --all --strict --no-interactive` passed.

## 2. Implementation
- [x] 2.1 Add a disabled-by-default realized equity drawdown guard to research gate config/state.
  - Evidence: `BacktestResearchGateConfig.max_realized_drawdown` defaults to `None`; `ResearchGateState` tracks realized and peak realized equity after completed trades only.
- [x] 2.2 Add exactly the three fixed named large-target drawdown-guard profiles.
  - Evidence: `EXIT_PROFILE_NAMES`, `research_gate_profile`, and `exit_profile_config` include the three `drawdown-30pct` profiles from the proposal.
- [x] 2.3 Preserve default/reference behavior and all non-selected profile settings.
  - Evidence: default guard is disabled; target/holding behavior reuses existing exit-profile config; targeted default gate test still passes.
- [x] 2.4 Serialize drawdown guard settings and skip counts in existing batch artifacts.
  - Evidence: `test_batch_runner_records_exit_profile` asserts `max_realized_drawdown=0.30` appears in risk-control settings; real `2024q1` summaries record `risk_control_settings` and `risk_control_skip_counts`.

## 3. Tests
- [x] 3.1 Add or update backtest tests for default-disabled behavior and causal skip after realized drawdown breach.
  - Evidence: `test_default_research_gates_are_noop`, `test_max_realized_drawdown_gate_blocks_after_realized_drawdown`, and validation test cover disabled/default and causal realized-state behavior.
- [x] 3.2 Add or update batch/profile tests for named profile resolution and serialization.
  - Evidence: `test_batch_runner_records_exit_profile` covers a drawdown-guard profile's exit settings and risk-control serialization.
- [x] 3.3 Run targeted tests covering drawdown guard and realistic-cost classification.
  - Evidence: targeted pytest for drawdown guard plus batch profile serialization passed 3 tests.

## 4. Quarterly experiment loop
- [x] 4.1 Run each fixed candidate with cached public data until a required realistic-cost quarter falsifies the candidate or all eight quarters pass.
  - Evidence: exact cached-data realistic-cost runs evaluated `2024q1` for all three candidates; each failed `2024q1` on `max_drawdown_below_threshold`, so none can reach required `8/8`.
- [x] 4.2 Record baseline or realistic pass/fail evidence for each candidate as required by the success gate.
  - Evidence: baseline scorecards were not run after realistic `2024q1` early falsification because success requires realistic-cost `8/8`; remaining required windows are marked blocked/not run in the scorecard.
- [x] 4.3 Run realistic-cost checks with `spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055`, and `funding_rate_per_bar=0.00001`.
  - Evidence: realistic summaries under `artifacts/equity-drawdown-guard-profile-comparison-realistic-smoke/.../summary.json`; combined early-falsified summary at `artifacts/equity-drawdown-guard-profile-comparison-summary/early-falsified/summary.json`.
- [x] 4.4 Update tasks with per-quarter status changes, blockers, metrics, and artifact paths.
  - Evidence: `artifacts/equity-drawdown-guard-profile-comparison-summary/early-falsified/scorecard.csv` records required windows; `2024q1` is failed for every candidate and remaining quarters are marked blocked/not run after early falsification.
- [x] 4.5 If no candidate reaches realistic-cost `8/8`, mark the hypothesis falsified and do not send success notification.
  - Verdict: falsified. `target-3p0-hold-32-drawdown-30pct` realistic `2024q1` failed drawdown (`net_profit=5411.55`, `profit_factor=1.3743`, `max_drawdown=-0.4626`); `target-4p0-hold-32-drawdown-30pct` failed drawdown (`net_profit=7025.37`, `profit_factor=1.4783`, `max_drawdown=-0.4597`); `close-target-2p0-hold-32-drawdown-30pct` failed drawdown (`net_profit=4296.02`, `profit_factor=1.3222`, `max_drawdown=-0.4788`). No success notification sent.

## 5. Verification and closure
- [x] 5.1 Run targeted and full pytest as appropriate.
  - Evidence: targeted pytest passed 3 tests; final `env UV_CACHE_DIR=.uv-cache uv run pytest` passed 119 tests.
- [x] 5.2 Run `uv run ruff check .`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run ruff check .` passed.
- [x] 5.3 Run `uv run pyright`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pyright` passed with 0 errors.
- [x] 5.4 Run strict OpenSpec validation for this change and all specs.
  - Evidence: strict change validation passed; `validate --all --strict --no-interactive` passed 11 items.
- [x] 5.5 Run `git diff --check` and duplicate spec/archive-name check.
  - Evidence: `git diff --check` passed; duplicate spec/archive-name check reported `intersection_count=0` before archive.
- [x] 5.6 Perform self-review for scope, no-lookahead, threshold preservation, artifact completeness, and secret safety.
  - Review: implementation only adds one disabled-by-default realized-state drawdown guard and three explicit research-only large-target drawdown profiles; guard uses completed-trade equity state before future entries, not current/future trade outcome; thresholds, quarters, public cached data scope, and realistic-cost settings are preserved. `2024q1` early-falsifies all candidates on drawdown, so the score did not reach `8/8` and no success notification was sent.
- [x] 5.7 Archive the completed change as success or falsified research evidence before commit.
  - Evidence: archived as `openspec/changes/archive/2026-06-27-compare-breakout-equity-drawdown-guard-profiles`; archive warning reflected this closure checkbox being completed after archive.
- [x] 5.8 Create one scoped local commit if repository state is safe.
  - Evidence: repository state is safe for a scoped commit with unrelated `.dev/autonomous_dev.sh` intentionally left unstaged; final report records the created commit hash.
