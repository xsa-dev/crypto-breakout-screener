# Design

## Scope
Extend the archived BTCUSDT CSV-based experiment runner with a public historical data download path. The downloader is still part of the first crypto research pipeline: it fetches public OHLCV data for M15/H1/H4/D1, writes reproducible local CSV files, and hands the M15 CSV to the already implemented canonical `Bar` importer/backtest runner while retaining H1/H4/D1 context CSVs as reproducible datasets for later context-aware logic.

The required first slice remains:
- market: crypto;
- venue/source: public unauthenticated Bybit kline API unless implementation evidence selects another public source;
- symbol: BTCUSDT;
- instrument type: linear/perpetual;
- execution timeframe: M15;
- context timeframe datasets: H1/H4/D1 are required downloaded datasets alongside M15;
- output: local CSV plus existing report/export artifacts and dataset manifest;
- live trading/private account access: blocked.

## Provider contract
Use Bybit public v5 market klines as the initial source:
- HTTP GET `/v5/market/kline`;
- `category=linear` for BTCUSDT USDT perpetual/linear market;
- `symbol=BTCUSDT`;
- `interval=15` for M15, `60` for H1, `240` for H4, and `D` for D1;
- `start`/`end` in Unix milliseconds;
- `limit` at or below the provider maximum, currently documented as 1000.

The implementation should isolate provider-specific response parsing from the experiment runner. A small downloader module may live near `src/app/breakout/experiments/crypto_backtest.py`, or the existing module may be extended if it remains cohesive.

## Time range and pagination
The CLI must require an explicit start/end range or otherwise fail closed with a clear error. Open-ended downloads are out of scope for the first downloader.

Pagination rules:
1. Convert user start/end to timezone-aware UTC and provider milliseconds.
2. Request pages deterministically for each required timeframe until the requested range is covered or the provider returns no more bars.
3. Preserve only closed bars inside the requested range. If the provider returns a currently forming/latest candle for an end time near now, exclude it or mark it according to an explicit policy; the default should avoid incomplete candles for reproducibility.
4. Deduplicate by timestamp and sort ascending before writing CSV.
5. Detect gaps using the existing normalizer after import.
6. Record page count, response row count, accepted row count, requested range, fetched range, provider category, interval/timeframe, endpoint host/path, and warnings in source metadata for each timeframe.

## CSV output
The downloader should write one local CSV per required timeframe with the same columns consumed by `import_crypto_csv`:
- `timestamp` as UTC ISO-8601 with `Z` or equivalent timezone-aware representation;
- `open`;
- `high`;
- `low`;
- `close`;
- `volume`;
- optional `source`/`spread` only if compatible with the importer.

Prefer a deterministic path under an ignored directory such as:

`artifacts/market-data/bybit/linear/BTCUSDT/<timeframe>/<start>_<end>.csv`

The path may be configurable, but generated market-data files must remain ignored unless a small test fixture is intentionally committed.

## Runner integration
Expose one or both CLI modes:
1. download-only: fetch public data and write CSV files;
2. download-and-run: fetch public data, write CSV files, then call `run_crypto_experiment` with the M15 CSV and record H1/H4/D1 CSV paths as context datasets.

The command should remain `uv run` friendly and fetch all four required timeframes for the range, for example:

`uv run python -m src.app.breakout.experiments.crypto_backtest --download-public bybit --timeframes M15,H1,H4,D1 --start 2024-01-01T00:00:00Z --end 2024-01-02T00:00:00Z --output-dir artifacts/backtests`

Exact flag names can change during implementation, but the final command must be documented in tests/tasks and must not require credentials.

## Error and rate-limit behavior
The downloader should handle:
- non-200 HTTP responses;
- provider retCode/error payloads;
- empty results;
- malformed rows;
- duplicate/out-of-order rows;
- request timeout;
- explicit rate-limit/backoff boundaries.

Keep behavior simple and deterministic: bounded retries with small backoff are acceptable; infinite loops and long-running pollers are not. Any failed public download should fail with an explicit error and no partial report claim. If a CSV was partially written, it should either be written atomically after full success or clearly marked as partial and not fed into the runner.

## Safety and secrets
The downloader must not import `src.core.env`, read `.env`, read exchange API key fields, add authorization headers, or call private endpoints. Tests should set fake private env vars and assert they do not appear in CSV, manifest, report JSON, logs, or source metadata.

## Verification notes
Network availability is not guaranteed in every development environment. The implementation must include mocked HTTP tests for deterministic behavior. A real public smoke should be run when network/provider access is available; if unavailable or rate-limited, record the exact blocker and still run the mocked fixture smoke and existing local runner smoke.
