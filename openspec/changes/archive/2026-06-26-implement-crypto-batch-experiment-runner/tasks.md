## 1. OpenSpec readiness
- [x] 1.1 Confirm scope is limited to BTCUSDT crypto batch research over explicit historical windows using public unauthenticated Bybit data.
- [x] 1.2 Confirm non-goals: no live trading, private API, FX, ETH/top-N, optimization, OOS approval, UI, scheduler, deployment, or database persistence.
- [x] 1.3 Validate this change strictly and validate all OpenSpec specs before source edits.

## 2. Batch runner implementation
- [x] 2.1 Add a local batch runner module or CLI mode that orchestrates existing public download + `run_crypto_experiment` per window.
- [x] 2.2 Support a named first-pass window preset and/or explicit user-provided windows file/list.
- [x] 2.3 For each window, download/reuse BTCUSDT M15/H1/H4/D1 public data and run the existing M15 backtest path.
- [x] 2.4 Record per-window status, blocker/error reason, manifest path, artifact directory, downloaded CSV paths, dataset hash, config hash, and metrics.
- [x] 2.5 Write deterministic batch summary CSV and JSON artifacts under an ignored output directory.
- [x] 2.6 Keep generated market-data and report artifacts ignored/protected from accidental commits.

## 3. Research verdict and thresholds
- [x] 3.1 Implement visible research thresholds for the batch screen, distinct from production OOS approval thresholds.
- [x] 3.2 Mark `technical_pass` only when required windows complete with datasets, manifests, metrics, and no feed gaps.
- [x] 3.3 Mark hypothesis support only when all required windows satisfy the configured research thresholds.
- [x] 3.4 Mark hypothesis not supported when any required window fails, has feed gaps, no trades, missing metrics, or fails thresholds.
- [x] 3.5 Ensure output explicitly says the verdict is research-only and not production trading approval.

## 4. Safety and failure behavior
- [x] 4.1 Ensure the batch runner does not read `.env`, import `src.core.env`, use API keys, set authorization headers, call private endpoints, or print secrets.
- [x] 4.2 Implement explicit behavior for failed windows: fail-fast or failed-row continue, with tests proving failed windows are not marked passed.
- [x] 4.3 Ensure partial failed downloads/backtests do not produce a passed row or aggregate hypothesis-supported verdict.

## 5. Tests
- [x] 5.1 Test mocked multi-window batch execution without network.
- [x] 5.2 Test summary CSV/JSON determinism and required columns/fields.
- [x] 5.3 Test threshold/verdict logic for supported, not-supported, and technical-failure cases.
- [x] 5.4 Test that per-window context timeframe CSV paths and availability are included in the summary.
- [x] 5.5 Test fake private env vars/credentials are not required, read, or emitted into summaries/manifests/logs.
- [x] 5.6 Test partial-window failure behavior.

## 6. Verification and review
- [x] 6.1 Run targeted batch runner tests.
- [x] 6.2 Run existing crypto experiment tests.
- [x] 6.3 Run `uv run pytest`.
- [x] 6.4 Run `uv run ruff check .`.
- [x] 6.5 Run `uv run pyright`.
- [x] 6.6 Run `npx --yes @fission-ai/openspec@1.4.1 validate implement-crypto-batch-experiment-runner --strict --no-interactive`.
- [x] 6.7 Run `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`.
- [x] 6.8 Run `git diff --check`.
- [x] 6.9 Run one real public BTCUSDT batch smoke with a short explicit window set when network/provider access is available, or record the exact skip blocker and run mocked fixture smoke.
- [x] 6.10 Self-review that the output answers a research screening question and does not claim production readiness.
