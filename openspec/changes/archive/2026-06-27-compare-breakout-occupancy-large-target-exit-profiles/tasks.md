## 1. OpenSpec readiness
- [x] 1.1 Record active/unrelated dirty files and confirm this change is the selected BTCUSDT owner-goal work. Evidence: pre-existing `.dev/autonomous_dev.sh` modification and unrelated untracked `openspec/changes/evaluate-breakout-altcoin-universe-profiles/` were left untouched; this change targets BTCUSDT path-risk/exit/holding.
- [x] 1.2 Record the pre-change quarterly scorecard, failing quarters, thresholds, artifact path, and verification command. Evidence: proposal records reference `5/8`, failing `2024q1`, `2024q2`, `2024q4`, thresholds, and artifact path.
- [x] 1.3 Validate this change strictly before source implementation. Evidence: `npx --yes @fission-ai/openspec@1.4.1 validate compare-breakout-occupancy-large-target-exit-profiles --strict --no-interactive` passed.

## 2. Implementation
- [x] 2.1 Add fixed occupancy large-target profile names to the batch runner. Evidence: `EXIT_PROFILE_NAMES` includes `occupancy-target-4p0-hold-32` and `occupancy-close-target-2p0-hold-32`.
- [x] 2.2 Map the profiles to existing occupancy gate and target/close-target exit settings without changing default behavior. Evidence: existing `-occupancy-` gate detection sets `block_overlapping_positions=true`; `exit_profile_config` maps the two names to `target_atr=4.0` and `close_target_atr=2.0`.
- [x] 2.3 Preserve BTCUSDT default behavior and existing BTCUSDT tests. Evidence: only fixed profile mappings were added; targeted existing exit-profile test passed.

## 3. Tests
- [x] 3.1 Add/extend tests that occupancy large-target profiles serialize deterministic gate and exit settings. Evidence: `tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile` covers both new profile names.
- [x] 3.2 Add/confirm tests that default non-occupancy exit behavior remains unchanged. Evidence: existing assertions in the same test still cover non-occupancy target/close-target profiles and the targeted test passed.

## 4. Quarterly experiment loop
- [x] 4.1 Run BTCUSDT `2024q1` early-falsification for each candidate under unchanged realistic costs. Evidence: ran both candidates with `--spread 1.0 --slippage 0.5 --commission-rate 0.00055 --funding-rate-per-bar 0.00001` and cached public data.
- [x] 4.2 Promote any candidate that passes `2024q1` to full `2023q1..2024q4` quarterly scorecard. Evidence: no candidate passed `2024q1`; full promotion was not justified.
- [x] 4.3 Record per-quarter pass/fail/blocked status, blockers, metrics, and artifact paths. Evidence: `artifacts/occupancy-large-target-exit-profile-comparison/early-falsified/summary.json` and `scorecard.csv`; `occupancy-target-4p0` net `33633.68`, PF `1.1290`, max DD `-0.8554`, blocker `max_drawdown_below_threshold`; `occupancy-close-target-2p0` net `10103.12`, PF `1.0345`, max DD `-1.4011`, blocker `max_drawdown_below_threshold`.
- [x] 4.4 State whether the score moved from the reference `5/8` toward `8/8`. Evidence: no pass-count movement; both candidates failed the primary `2024q1` blocker quarter, so the hypothesis is falsified/negative evidence.

## 5. Verification and closure
- [x] 5.1 Run targeted pytest. Evidence: `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_crypto_batch_experiment.py::test_batch_runner_records_exit_profile` passed.
- [x] 5.2 Run full relevant pytest if source behavior changed broadly. Evidence: `env UV_CACHE_DIR=.uv-cache uv run pytest` passed `125 passed`.
- [x] 5.3 Run `uv run ruff check .`. Evidence: `env UV_CACHE_DIR=.uv-cache uv run ruff check .` passed.
- [x] 5.4 Run `uv run pyright`. Evidence: `env UV_CACHE_DIR=.uv-cache uv run pyright` passed with `0 errors, 0 warnings`.
- [x] 5.5 Run strict OpenSpec validation for this change and all specs. Evidence: `validate compare-breakout-occupancy-large-target-exit-profiles --strict --no-interactive` and `validate --all --strict --no-interactive` passed.
- [x] 5.6 Run `git diff --check` and duplicate spec/archive-name check. Evidence: `git diff --check` passed; duplicate spec/archive-name check reported `0` before archive.
- [x] 5.7 Archive as success only if one candidate reaches required `8/8`; otherwise archive as falsified/negative research evidence. Evidence: both candidates failed `2024q1` on `max_drawdown_below_threshold`; archive as falsified/negative research evidence.
- [x] 5.8 Create one scoped local commit if repository state is safe. Evidence: archive-ready scoped changes are isolated for a local commit after archive; unrelated `.dev/autonomous_dev.sh` and `openspec/changes/evaluate-breakout-altcoin-universe-profiles/` remain unstaged and excluded.
