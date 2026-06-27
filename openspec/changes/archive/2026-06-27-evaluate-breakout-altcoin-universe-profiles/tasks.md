## 1. OpenSpec readiness
- [x] 1.1 Confirm no active OpenSpec changes and record unrelated dirty files. Active change: `evaluate-breakout-altcoin-universe-profiles`; unrelated pre-existing dirty file kept out of scope: `.dev/autonomous_dev.sh`.
- [x] 1.2 Record the BTCUSDT large-target and scaled-exposure evidence motivating the symbol-universe shift in `proposal.md`/`design.md`.
- [x] 1.3 Validate this change strictly before source implementation: `npx --yes @fission-ai/openspec@1.4.1 validate evaluate-breakout-altcoin-universe-profiles --strict --no-interactive` passed.

## 2. Implementation
- [x] 2.1 Add a fixed approved public crypto research symbol allowlist with BTCUSDT default and 50 non-BTC altcoin candidates.
- [x] 2.2 Generalize downloader and batch validation to accept only approved symbols while still rejecting unsupported/private scopes.
- [x] 2.3 Update batch summary typing/serialization so non-BTCUSDT symbols are recorded correctly.
- [x] 2.4 Preserve BTCUSDT default behavior and existing BTCUSDT tests.
- [x] 2.5 Record unavailable/missing-history symbols as explicit blocked evidence rather than silently substituting another symbol.
- [x] 2.6 Add a shared-bankroll portfolio evaluation mode with `starting_equity=10000`, fixed per-trade notional cap, fixed total exposure cap, and one combined equity curve.
- [x] 2.7 Record per-symbol contribution reports alongside portfolio-level quarterly summaries.
- [x] 2.8 Add deterministic market-regime labeling for promoted portfolio runs, including `bull_long`, `bear_short_or_avoid`, and `neutral_blocked`.
- [x] 2.9 Record per-regime PnL, trade count, drawdown contribution, skipped/blocked signals, and the long/short-or-avoid decision used by the portfolio scorecard.
- [x] 2.10 Treat incomplete symbol data/blank metrics as technical blockers instead of successful technical evidence. Blank numeric metrics now become explicit `missing_*` blockers, and portfolio windows with symbol data failures set `technical_pass=false`.

## 3. Tests
- [x] 3.1 Add tests that ETHUSDT is accepted for public-data research downloads/batches.
- [x] 3.2 Add tests that unsupported symbols still fail closed with an explicit validation error.
- [x] 3.3 Add tests that batch summaries serialize the selected symbol and artifact paths under `crypto/<symbol>/...`.
- [x] 3.4 Add tests that the fixed 50-symbol universe is deterministic and contains no dynamic market-cap/network lookup.
- [x] 3.5 Add tests proving portfolio mode uses one `10000 USDT` bankroll, not one independent deposit per symbol.
- [x] 3.6 Add tests proving simultaneous symbol signals cannot exceed the configured total portfolio exposure cap.
- [x] 3.7 Add tests proving regime labels are deterministic for the same OHLCV context.
- [x] 3.8 Add tests proving bearish or ambiguous regimes cannot be counted as long-edge success without an explicit regime rule.
- [x] 3.9 Add regression tests that blank metrics are recorded as missing-metric blockers and portfolio symbol failures prevent technical pass.

## 4. Quarterly experiment loop
- [x] 4.1 Run ETHUSDT as a single-symbol data proof for `target-4p0-hold-32` under realistic costs. Evidence: `artifacts/altcoin-universe-portfolio-comparison/conservative-v1-m15-slope-positive-max-trades-8-target-4p0-hold-32/c839eef3e2c53165/summary.json` (`2024q1` smoke blocked on net/PF: net `-72.13`, PF `0.9656`, DD `-0.0458`).
- [x] 4.2 Run portfolio smoke/early-falsification for the fixed 50-symbol altcoin allowlist using `starting_equity=10000`. Evidence before regime rule: `artifacts/altcoin-universe-portfolio-comparison/conservative-v1-m15-slope-positive-max-trades-8-target-4p0-hold-32/6c6afa95094d94dc/summary.json` (`2024q1` blocked: net `-6674.47`, PF `0.2238`, DD `-0.6674`, symbol blockers present).
- [x] 4.3 Promote any portfolio profile that passes its blocker-quarter smoke to a full `2023q1..2024q4` portfolio scorecard. No profile was promoted: the regime-aware fixed-50 `target-4p0` blocker-quarter smoke failed `2024q1` well below thresholds, so the approved early-falsification gate stopped before an eight-quarter promoted run.
- [x] 4.4 Record portfolio pass/fail status, net profit in USDT, profit factor, max drawdown relative to `10000`, safety buffer to thresholds, and artifact paths. Regime-aware `target-4p0` evidence before ledger-report fix: `artifacts/altcoin-universe-portfolio-comparison-regime-smoke-valid/conservative-v1-m15-slope-positive-max-trades-8-target-4p0-hold-32/6c6afa95094d94dc/summary.json` (`2024q1` blocked: net `-9799.61`, PF `0.1283`, DD `-0.9800`, accepted trades `788`, skipped/blocked regime/exposure signals `1564`, blocked symbols `43`). Re-aggregated evidence with explicit threshold buffers and corrected technical-pass status: `artifacts/altcoin-universe-portfolio-comparison-regime-smoke-reaggregated-ledger-fix/conservative-v1-m15-slope-positive-max-trades-8-target-4p0-hold-32/520b158e637db140/summary.json` (`2024q1` blocked: net buffer `-9799.61`, PF buffer `-0.8717`, DD buffer `-0.6300`, technical_pass `false`). Baseline quarterly scorecard before this ledger-report fix: `2023q1..2023q4`, `2024q2..2024q4` unknown/not promoted; `2024q1` blocked by net/PF/DD and symbol blockers.
- [x] 4.5 Record per-symbol contribution, blockers, missing-history symbols, and top positive/negative contributors in portfolio `per-symbol-contributions.csv` artifacts.
- [x] 4.6 Record per-regime contribution and explicitly state whether each regime is long-enabled, short-side research only, or risk-off/blocked. Evidence: `artifacts/altcoin-universe-portfolio-comparison-regime-smoke-valid/conservative-v1-m15-slope-positive-max-trades-8-target-4p0-hold-32/6c6afa95094d94dc/per-regime-contributions.csv`; bull_long accepted `788` with PnL `-9799.61`, bear_short_or_avoid risk-off skipped `302`, neutral_blocked skipped `646`.

## 5. Verification and closure
- [x] 5.1 Run targeted pytest: `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_crypto_batch_experiment.py tests/test_crypto_historical_experiment.py -q` passed (`28 passed`).
- [x] 5.2 Run full relevant pytest if source behavior changed broadly: `env UV_CACHE_DIR=.uv-cache uv run pytest -q` passed (`131 passed`).
- [x] 5.3 Run `uv run ruff check .`: passed.
- [x] 5.4 Run `uv run pyright`: passed (`0 errors`).
- [x] 5.5 Run strict OpenSpec validation for this change and all specs: passed (`11 items`).
- [x] 5.6 Run `git diff --check` and duplicate spec/archive-name check: both passed; duplicate count `0`.
- [x] 5.7 Archive as success only if one shared-bankroll portfolio profile reaches realistic-cost `8/8` with buffer and regime reporting; otherwise archive as falsified/negative research evidence. Verdict: falsified/negative evidence. No evaluated portfolio profile reached the blocker-quarter smoke gate for promotion; `target-4p0` fixed-50 `2024q1` remained blocked after realistic costs and regime reporting, so no success notification is allowed.
- [x] 5.8 Create one scoped local commit if repository state is safe. Ready for archive-then-commit; `.dev/autonomous_dev.sh` remains an unrelated dirty file outside this OpenSpec scope and must stay unstaged.
