# implement-crypto-historical-experiment-runner

## Why
The breakout strategy now has market-agnostic canonical data, deterministic backtesting, and local report exports, but the first real experiment still needs a safe, reproducible path from public crypto historical market data to a backtest report artifact. The first experiment should answer only whether the system can load real crypto data, normalize it into canonical `Bar` records, run the existing strategy replay, and export auditable artifacts.

## What Changes
- Add a first crypto historical experiment runner for BTCUSDT perpetual/futures research using public unauthenticated market data only.
- Support deterministic loading of historical OHLCV bars through a CSV importer and, if feasible within the same implementation slice, a public downloader/provider path. The implementation may ship CSV-only first when that is the narrowest reproducible path; any network downloader must remain public and credential-free.
- Normalize bars into the existing canonical `Bar` contract, including UTC timestamps, deterministic ordering/deduplication, OHLC validation, gap diagnostics, and source metadata.
- Produce a dataset manifest per run with source, market, instrument type, symbol, timeframe, date range, bar count, dataset hash, gaps, normalization warnings, generated timestamp, and source metadata.
- Add a crypto cost-model configuration for BTCUSDT perpetual research with explicit spread, slippage, fee/commission assumptions, and funding assumption or an explicit unavailable/deferred reason.
- Add a CLI/script entrypoint that runs the experiment, exports the existing backtest report artifacts plus dataset manifest, and prints a concise summary with run id, hashes, bars, metrics, and artifact paths.
- Define an optional container execution wrapper for the experiment so the same command can be run in an isolated, reproducible local runtime without introducing production deployment scope.

## Non-Goals
- No live orders, live broker/exchange execution, order submission, cancellation, modification, or position synchronization.
- No Bybit/private API credentials, private account data, balances, equity, order history, or private account state.
- No semi-auto operator confirmation flow and no production full-auto approval.
- No concrete live execution adapter or broker reconciliation adapter.
- No FX, XAUUSD, EURUSD, CFD, stock, or multi-market experiment in this change.
- No production readiness claim, production OOS GO, or walk-forward production approval.
- No parameter optimization, top-N batch runner, ETHUSDT expansion, or multi-period portfolio conclusion.
- No UI/operator dashboard work.
- No production container deployment, registry publishing, cloud runtime, Kubernetes, VPS/systemd changes, or live long-running service container.

## Acceptance Criteria
- A reviewed first experiment scope is encoded as crypto-only, BTCUSDT, futures/perpetual, M15 execution timeframe, H1/H4/D1 context timeframe metadata, public unauthenticated data, and report/export-artifact output.
- The implementation can run without API keys or private account data; tests prove credential fields are not required or read for the experiment path.
- Historical bars are normalized to canonical `Bar` records with UTC timestamps, deterministic deduplication/ordering, OHLC validation, gap diagnostics, and source metadata.
- Each run writes a deterministic dataset manifest that links to the backtest report via dataset hash/run metadata.
- The runner uses explicit crypto cost assumptions and marks missing funding or other unavailable production-quality inputs as research limitations rather than production approval.
- The runner exports the existing report artifacts and dataset manifest under a local artifacts/reports directory that is ignored or otherwise protected from accidental large artifact commits.
- If a container wrapper is implemented, it runs the same public-data historical experiment command, mounts only explicit input/output paths, does not mount `.env` or credential files, and produces the same deterministic artifacts as the host `uv run` path.
- Verification includes targeted tests, full pytest, Ruff, Pyright, strict OpenSpec validation, `git diff --check`, and one real BTCUSDT experiment command using fixture/public data to produce an actual report artifact.
