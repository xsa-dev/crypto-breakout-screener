## 1. OpenSpec readiness
- [x] 1.1 Record unrelated dirty files and active changes outside the BTCUSDT owner goal.
  - Evidence: pre-change `git status --short --branch` showed unrelated modified `.dev/autonomous_dev.sh` and untracked `openspec/changes/evaluate-breakout-altcoin-universe-profiles/`; both were left untouched.
- [x] 1.2 Record the pre-change BTCUSDT quarterly scorecard and failed-window blockers.
  - Evidence: proposal records reference `5/8`, passes `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q3`, and failures `2024q1`, `2024q2`, `2024q4` from `artifacts/realistic-cost-profile-search/conservative-v1-m15-slope-positive-max-trades-8/scorecard.csv`.
- [x] 1.3 Validate this change strictly before source implementation.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 validate compare-breakout-large-target-breakeven-exit-profiles --strict --no-interactive` passed.

## 2. Implementation
- [x] 2.1 Add the three fixed large-target + break-even profile names to the batch runner allowlist.
- [x] 2.2 Map each profile to deterministic `BacktestExitProfileConfig` settings.
- [x] 2.3 Preserve default BTCUSDT behavior and existing profile mappings.

## 3. Tests
- [x] 3.1 Add tests for the new profile settings.
- [x] 3.2 Run targeted pytest for crypto batch profile mapping.
  - Evidence: RED failed before implementation with unsupported gate profile; GREEN `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile -q` passed.

## 4. Quarterly experiment loop
- [x] 4.1 Run `2024q1` realistic-cost early-falsification for all three candidates.
  - Evidence command: `env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.crypto_batch --windows '2024q1:2024-01-01T00:00:00Z/2024-04-01T00:00:00Z' --gate-profile <candidate> --reuse-market-data --market-data-dir artifacts/feature-diagnostics-market-data --output-dir artifacts/large-target-breakeven-exit-profile-comparison/q1-smoke-<candidate> --spread 1.0 --slippage 0.5 --commission-per-unit 0.0 --funding-per-bar 0.0 --commission-rate 0.00055 --funding-rate-per-bar 0.00001`.
- [x] 4.2 Promote any `2024q1` passing candidate to full `2023q1..2024q4` scorecard.
  - Evidence: no candidate passed `2024q1`; none were promoted.
- [x] 4.3 Record scorecard statuses, net profit, profit factor, max drawdown, blockers, and artifact paths.
  - Evidence: `artifacts/large-target-breakeven-exit-profile-comparison/early-falsified/summary.json` and `artifacts/large-target-breakeven-exit-profile-comparison/early-falsified/scorecard.csv`.
  - `target-3p0-breakeven-1p0-hold-32`: `2024q1` failed, net `132472.25699314324`, PF `1.475928833846155`, max drawdown `-0.8443936134692805`, blocker `max_drawdown_below_threshold`.
  - `target-4p0-breakeven-1p0-hold-32`: `2024q1` failed, net `166423.59527314323`, PF `1.601348107681768`, max drawdown `-1.4313035932726113`, blocker `max_drawdown_below_threshold`.
  - `close-target-2p0-breakeven-1p0-hold-32`: `2024q1` failed, net `95260.3008840004`, PF `1.334442905746348`, max drawdown `-0.8225569608245572`, blocker `max_drawdown_below_threshold`.
- [x] 4.4 State whether the score moved from reference `5/8` toward `8/8`.
  - Verdict: not supported; the primary failing quarter `2024q1` remained failed for all candidates, so the hypothesis did not move the score toward `8/8`.

## 5. Verification and closure
- [x] 5.1 Run relevant pytest.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_crypto_batch_experiment.py -q` passed `15` tests.
- [x] 5.2 Run `uv run ruff check .`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run ruff check .` passed.
- [x] 5.3 Run `uv run pyright`.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pyright` reported `0 errors`.
- [x] 5.4 Run strict OpenSpec validation for this change and all specs.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 validate compare-breakout-large-target-breakeven-exit-profiles --strict --no-interactive` passed; `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive` passed `12` items.
- [x] 5.5 Run `git diff --check` and duplicate spec/archive-name check.
  - Evidence: pre-archive `git diff --check` passed; duplicate spec/archive-name check will be rerun after archive.
- [x] 5.6 Archive as success only if one candidate reaches realistic-cost `8/8`; otherwise archive as falsified/negative research evidence.
  - Verdict before archive: no candidate reached `8/8`; archive this change as falsified/negative research evidence and do not send success notification.
- [x] 5.7 Create one scoped local commit if repository state is safe.
  - Evidence: repository state is safe for a scoped local commit after archive; unrelated `.dev/autonomous_dev.sh` and `evaluate-breakout-altcoin-universe-profiles` remain unstaged/out of scope.
