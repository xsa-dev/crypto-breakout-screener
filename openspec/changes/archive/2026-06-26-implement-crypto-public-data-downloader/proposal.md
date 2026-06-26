# implement-crypto-public-data-downloader

## Why
The first crypto historical experiment runner can already replay a BTCUSDT M15 CSV fixture into deterministic backtest artifacts, but it still requires a pre-existing CSV file. To run real first experiments on fresh BTCUSDT public market history, the project needs a credential-free downloader that fetches public historical OHLCV bars for M15/H1/H4/D1, writes reproducible local CSV dataset inputs, and then uses the existing importer/runner path.

## What Changes
- Add a public unauthenticated crypto historical OHLCV downloader for the BTCUSDT first-slice experiment.
- Use Bybit public market kline data as the initial venue/source for BTCUSDT USDT perpetual/linear history unless implementation evidence shows a smaller compatible public source is safer.
- Support M15 as the required execution timeframe and H1/H4/D1 as required context timeframe datasets. The first backtest runner may still consume M15 only until context-aware strategy logic exists, but the downloader must fetch and persist all four timeframe series for the same requested range.
- Page through public kline responses deterministically across a requested UTC start/end range, respecting provider page-size/rate-limit constraints.
- Write normalized raw-data CSV files that the existing `import_crypto_csv` path can consume, then optionally run the existing `run_crypto_experiment` command on the M15 execution dataset in the same CLI flow while retaining H1/H4/D1 as downloaded context datasets.
- Record downloader source metadata and provider diagnostics in the dataset manifest without API keys, private headers, account data, or `.env` values.

## Non-Goals
- No private Bybit API, signed requests, API keys, balances, positions, order history, or account state.
- No live orders, live execution adapter, broker reconciliation, semi-auto confirmation, or full-auto production approval.
- No FX/XAUUSD/EURUSD, multi-market support, ETHUSDT/top-N batch runs, optimization, or production OOS approval in this change.
- No container wrapper implementation unless it is a trivial reuse of the existing host command and does not add production deployment behavior.
- No database persistence, admin UI, scheduler, long-running service, or deployment automation.
- No new dependency unless the approved implementation proves the existing `aiohttp` dependency is insufficient.

## Acceptance Criteria
- A user can run a `uv run` command that fetches BTCUSDT M15/H1/H4/D1 public historical OHLCV data for an explicit UTC start/end range without credentials.
- The downloader writes deterministic local CSV input under an ignored artifact/data directory and can feed the existing crypto experiment runner.
- Repeating the same download for the same provider responses, range, symbol, timeframes, and pagination settings produces the same CSV contents and dataset hashes, aside from generated-at metadata in manifests.
- Provider pagination, ordering, duplicate handling, incomplete/latest candle handling, and empty/error responses are explicit and tested.
- Downloader diagnostics identify provider/source, category/instrument type, symbol, intervals, requested range, fetched ranges, page counts, row counts, and any gaps/warnings without secrets.
- Tests cover public-response parsing with mocked HTTP, pagination, deterministic CSV writing, no credential requirement, and integration with the existing runner/importer on downloaded fixture data, including M15 backtest input and H1/H4/D1 context CSV outputs.
- Verification includes targeted downloader tests, full pytest, Ruff, Pyright, strict OpenSpec validation, `git diff --check`, and one real or explicitly skipped public BTCUSDT download smoke. If network/provider access is unavailable, the skip reason must be recorded and a mocked fixture smoke must still produce artifacts.
