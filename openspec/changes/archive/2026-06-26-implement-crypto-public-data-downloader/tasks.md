## 1. OpenSpec readiness
- [x] 1.1 Confirm the downloader scope is limited to BTCUSDT M15/H1/H4/D1 public historical OHLCV data and does not include private API, live trading, FX, batch symbols, UI, or deployment work.
- [x] 1.2 Validate this change strictly and validate all OpenSpec specs before source edits.
- [x] 1.3 Confirm generated market-data CSV/output directories are ignored or otherwise protected from accidental commits.

## 2. Public downloader implementation
- [x] 2.1 Add a provider-isolated public kline downloader for BTCUSDT linear/perpetual M15/H1/H4/D1 data.
- [x] 2.2 Require explicit UTC start/end inputs and reject open-ended or invalid ranges.
- [x] 2.3 Implement deterministic per-timeframe pagination with provider limit/page metadata and no infinite loops.
- [x] 2.4 Parse provider kline rows into deterministic OHLCV rows and reject/report malformed provider payloads.
- [x] 2.5 Deduplicate by timestamp, order ascending, and exclude or explicitly handle incomplete/latest candles.
- [x] 2.6 Write one output CSV per required timeframe atomically under an ignored local artifact/data directory.
- [x] 2.7 Record per-timeframe provider diagnostics/source metadata without secrets.

## 3. Runner integration
- [x] 3.1 Add CLI flags/mode for download-only and/or download-and-run through the existing crypto experiment runner, requiring M15/H1/H4/D1 by default.
- [x] 3.2 Ensure downloaded CSV files use columns accepted by `import_crypto_csv` and produces canonical `Bar` records without a second custom normalization path.
- [x] 3.3 Ensure dataset manifest/report metadata identifies source as public provider data rather than fixture CSV when using the downloader and includes all downloaded timeframe CSV paths.
- [x] 3.4 Keep BTCUSDT first-slice scope guard intact; M15 remains the execution/backtest input while H1/H4/D1 are required downloaded context datasets.

## 4. Error handling and safety
- [x] 4.1 Handle non-200 HTTP responses, provider error payloads, empty pages, malformed rows, and timeout/rate-limit cases with explicit errors.
- [x] 4.2 Use bounded retry/backoff only; do not add long-running services, schedulers, or polling daemons.
- [x] 4.3 Ensure downloader does not read `.env`, import `src.core.env`, use API keys, set authorization headers, call private endpoints, or print secrets.
- [x] 4.4 Preserve clean failure semantics: no partial CSV is fed into the runner as a completed dataset.

## 5. Tests
- [x] 5.1 Test provider response parsing with mocked public HTTP payloads.
- [x] 5.2 Test pagination across multiple mocked pages and multiple timeframes with deterministic ordering/deduplication.
- [x] 5.3 Test explicit start/end validation and incomplete/latest candle handling policy.
- [x] 5.4 Test deterministic per-timeframe CSV writing and integration with `import_crypto_csv`.
- [x] 5.5 Test download-and-run or documented download-only flow produces existing report artifacts from mocked downloaded data.
- [x] 5.6 Test fake private env vars/credentials are not required, read, or emitted into CSV/manifest/report metadata.
- [x] 5.7 Test provider errors, empty results, and malformed rows fail with explicit exceptions.

## 6. Verification and review
- [x] 6.1 Run targeted downloader tests.
- [x] 6.2 Run existing crypto experiment tests.
- [x] 6.3 Run `uv run pytest`.
- [x] 6.4 Run `uv run ruff check .`.
- [x] 6.5 Run `uv run pyright`.
- [x] 6.6 Run `npx --yes @fission-ai/openspec@1.4.1 validate implement-crypto-public-data-downloader --strict --no-interactive`.
- [x] 6.7 Run `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`.
- [x] 6.8 Run `git diff --check`.
- [x] 6.9 Run one real public BTCUSDT download smoke when network/provider access is available: `uv run python -m src.app.breakout.experiments.crypto_backtest --download-public bybit --start 2024-01-01T00:00:00Z --end 2024-01-03T00:00:00Z --market-data-dir artifacts/public-smoke-market-data --output-dir artifacts/public-smoke-backtests`.
- [x] 6.10 Run one end-to-end experiment using downloaded BTCUSDT data and record the CSV paths plus report/manifest artifact path: `artifacts/public-smoke-backtests/crypto/BTCUSDT/80cba3287b3150b4/80cba3287b3150b4-dataset-manifest.json`.
- [x] 6.11 Self-review that output proves only public-data historical research reproducibility, not production trading readiness.
