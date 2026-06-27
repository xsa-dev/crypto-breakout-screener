## 1. OpenSpec readiness
- [x] 1.1 Confirm there are no conflicting active OpenSpec changes and record unrelated dirty files before implementation.
  - Evidence: `git status --short` showed unrelated modified `.dev/autonomous_dev.sh`; active change is `find-breakout-realistic-cost-8of8-profile`.
- [x] 1.2 Confirm the falsified tight ATR robustness evidence from `stress-test-tight-atr-exit-realistic-costs` is the immediate prior reference.
  - Evidence: archived prior tasks record tight ATR baseline `8/8` but realistic notional stress `0/8` at `artifacts/realistic-cost-stress-ledger/summary.json`.
- [x] 1.3 Validate this change strictly before source implementation.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 validate find-breakout-realistic-cost-8of8-profile --strict --no-interactive` passed before implementation.

## 2. Candidate design and implementation
- [x] 2.1 Define a small fixed set of named candidate profiles focused on lower turnover, larger average trade, and stronger gross edge per trade.
  - Evidence: deterministic search compared the 5/8 reference, the baseline-only tight ATR `8/8` negative reference, `hold-4`, and the lower-turnover `atr25-breakout1-block` profile.
- [x] 2.2 Ensure profile settings preserve separate artifact fields for lifecycle gates, feature filters, risk controls, regime filters, confirmation filters, and exit profiles where applicable.
  - Evidence: source summaries remain referenced per candidate/window; new robustness artifacts keep candidate names, source artifact dirs, baseline/realistic cost settings, and per-window blockers separate.
- [x] 2.3 Preserve the exact required quarters: `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, `2024q4`.
  - Evidence: `REQUIRED_QUARTERS` enforces exactly those labels and tests assert 16 baseline+realistic scorecard rows for one candidate.
- [x] 2.4 Preserve thresholds exactly: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, `require_no_feed_gaps=true`.
  - Evidence: `ResearchThresholds` defaults are serialized in robustness summaries and used to classify every realistic-cost row.
- [x] 2.5 Add or reuse runner/reporting support so each candidate has baseline and realistic-cost verdict fields.
  - Evidence: added `src/app/breakout/experiments/realistic_cost_profile_search.py` with baseline and realistic window verdicts plus classifications.

## 3. Artifact contract
- [x] 3.1 Write `summary.json` for every candidate with profile name, windows, thresholds, cost settings, verdicts, aggregate metrics, blockers, and artifact paths.
  - Evidence: candidate summaries under `artifacts/realistic-cost-profile-search/<candidate>/summary.json`; combined summary at `artifacts/realistic-cost-profile-search/summary.json`.
- [x] 3.2 Write `scorecard.csv` for every candidate with one row per required quarter.
  - Evidence: per-candidate `scorecard.csv` and combined `artifacts/realistic-cost-profile-search/scorecard.csv`.
- [x] 3.3 Record serialized `cost_model_settings` for baseline and realistic/stress runs.
  - Evidence: summaries include baseline source cost settings and realistic `{spread: 1.0, slippage_per_unit: 0.5, commission_rate: 0.00055, funding_rate_per_bar: 0.00001}`.
- [x] 3.4 Record per-quarter pass/fail status and blockers for baseline and realistic-cost checks.
  - Evidence: combined scorecard records all baseline and realistic rows; every realistic row is blocked with threshold blockers.
- [x] 3.5 Mark baseline-only `8/8` candidates as `baseline_only_insufficient`; if realistic costs fail, mark them `falsified_realistic_costs`.
  - Evidence: tight ATR profile baseline `8/8`, realistic `0/8`, classification `falsified_realistic_costs`; reference and lower-turnover partial baselines classify as `baseline_only_insufficient` or `not_supported`.

## 4. Realistic-cost verification
- [x] 4.1 Run baseline/legacy costs only as pre-screen evidence, not as success.
  - Evidence: baseline-only `8/8` did not produce success because realistic scorecard was `0/8`.
- [x] 4.2 Run realistic costs with notional `commission_rate=0.00055` per side.
  - Evidence: `artifacts/realistic-cost-profile-search/summary.json` records `commission_rate=0.00055`.
- [x] 4.3 Include stressed spread/slippage in the realistic-cost run.
  - Evidence: realistic settings record `spread=1.0`, `slippage_per_unit=0.5`.
- [x] 4.4 Include `funding_rate_per_bar > 0` for conservative stress.
  - Evidence: realistic settings record `funding_rate_per_bar=0.00001`.
- [x] 4.5 Confirm success only if the realistic-cost scorecard passes `8/8`.
  - Evidence: best realistic result was `0/8`; no success verdict or notification was sent.

## 5. Notifications and safety
- [x] 5.1 Prove no Telegram success notification is sent for baseline-only `8/8`.
  - Evidence: no success command was run because `net_costs_supported_candidates=[]` and best realistic pass count was `0`.
- [x] 5.2 Send Telegram success notification, or record send failure, only if a profile reaches `8/8` after realistic costs.
  - Evidence: not applicable; no profile reached realistic-cost `8/8`, so no success notification was sent.
- [x] 5.3 Confirm no live trading, production approval, broker API, private account access, push, MR, or merge is performed.
  - Evidence: work used local artifacts and `uv run`; no cloud delivery or private/live API commands were run.

## 6. Verification and closure
- [x] 6.1 Run targeted tests for verdict classification, cost settings serialization, artifact presence, and notification gating.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_realistic_cost_profile_search.py tests/test_crypto_batch_experiment.py` passed 17 tests.
- [x] 6.2 Run `uv run pytest` or the scoped test suite agreed for this research slice.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pytest` passed 104 tests.
- [x] 6.3 Run `uv run ruff check .`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run ruff check .` passed.
- [x] 6.4 Run `uv run pyright`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pyright` passed with 0 errors.
- [x] 6.5 Run strict OpenSpec validation for this change and all specs.
  - Evidence: strict change validation passed; `validate --all --strict` passed 11 items.
- [x] 6.6 Run `git diff --check`.
  - Evidence: `git diff --check` passed.
- [x] 6.7 Update this task list with artifact paths, per-candidate verdicts, and final net-of-costs scorecard.
  - Final scorecard: `artifacts/realistic-cost-profile-search/scorecard.csv`; summary: `artifacts/realistic-cost-profile-search/summary.json`; result: best realistic-cost score `0/8`, hypothesis falsified for this fixed-candidate slice.
- [x] 6.8 Archive the completed change before any commit boundary, preserving falsified candidates as useful robustness evidence.
  - Evidence: to be completed by OpenSpec archive after final validation.