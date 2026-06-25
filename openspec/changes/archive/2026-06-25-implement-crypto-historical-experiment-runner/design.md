# Design

## Scope
Create the first safe historical crypto experiment path for the breakout strategy. The implementation should be narrow enough to produce a real, reproducible BTCUSDT report artifact, while preserving the existing market-agnostic architecture for later FX and multi-market work.

The approved first slice is:
- market: crypto;
- source zone: public unauthenticated market data only;
- first symbol: BTCUSDT;
- instrument type: futures/perpetual;
- execution timeframe: M15;
- context timeframe metadata: H1, H4, D1;
- output: deterministic backtest report/export artifacts plus dataset manifest;
- live trading/private account access: blocked.

## Data source approach
Use a deterministic CSV importer as the required first path because it is reproducible, testable without network, and does not require credentials. The importer should accept raw OHLCV rows with timestamp/open/high/low/close/volume and optional spread/source fields, then normalize them into canonical `Bar` records.

A public downloader/provider may be included only if it remains small, unauthenticated, and does not broaden the scope. If including both CSV and downloader would delay the first artifact, ship CSV/importer first and leave the public downloader to a follow-up change.

## Normalization and validation
Reuse and extend the existing canonical data boundary rather than introducing strategy-specific raw dicts between layers.

The experiment path must:
1. Parse provider/CSV rows into canonical `Bar` records.
2. Normalize timestamps to timezone-aware UTC.
3. Deduplicate bars deterministically by symbol/timeframe/timestamp.
4. Sort or reject out-of-order bars according to the explicit loader policy.
5. Validate OHLC invariants: `high >= open`, `high >= close`, `high >= low`, `low <= open`, `low <= close`, and `low <= high`.
6. Detect expected timeframe gaps and record them in the manifest.
7. Preserve source metadata where available.
8. Keep the backtest no-lookahead invariant: strategy evaluation at bar N only sees information that would have been available at that simulated timestamp.

## Dataset manifest
Each run should write a local manifest alongside the report artifacts. The manifest is part of the research artifact and should include:
- source (`csv`, `bybit_public`, `binance_public`, etc.);
- market (`crypto`);
- instrument type (`perpetual`/`futures`);
- symbol (`BTCUSDT` for the first run);
- execution timeframe (`M15`);
- context timeframes requested/available/unavailable (`H1`, `H4`, `D1`);
- start/end timestamps;
- number of bars;
- dataset hash;
- feed gaps;
- normalization warnings;
- generated-at timestamp;
- source file/API metadata without secrets.

The manifest must not contain API keys, private endpoint URLs, authorization headers, account identifiers, or `.env` values.

## Cost model
The runner must construct `BacktestConfig` with explicit non-zero crypto research costs. For BTCUSDT perpetual research, include:
- spread assumption;
- slippage assumption;
- commission/fee assumption;
- funding assumption or explicit unavailable/deferred reason.

If funding is unavailable, the report/manifest should make this a visible research limitation. The run may still be useful as a first reproducibility experiment, but it must not claim production acceptance quality for perpetual trading.

## Runner interface
Add a simple CLI or script entrypoint, for example:

`uv run python -m src.app.breakout.experiments.crypto_backtest --symbol BTCUSDT --timeframe M15 --csv <path> --output-dir artifacts/backtests`

The exact module/script name can follow project style, but it must be easy to run through `uv run` and should print a concise summary containing:
- run id;
- symbol;
- timeframe;
- bar count;
- dataset hash;
- config hash;
- trade count;
- net PnL or equivalent total metric;
- max drawdown;
- win rate;
- artifact paths, including dataset manifest.

## Optional container execution
The host `uv run` path remains the authoritative implementation and verification path. A container wrapper is useful for reproducibility and isolation, but it must not turn this change into deployment work.

If included, the container path should:
1. Run the same CLI command as the host path.
2. Mount only explicit read-only input data paths and explicit writable output artifact paths.
3. Avoid mounting `.env`, SSH keys, exchange credentials, shell history, or the whole home directory.
4. Use public unauthenticated data only.
5. Keep generated artifacts outside the image and under the ignored local artifact directory.
6. Prove parity with the host path by producing the same dataset hash and deterministic report identifiers on the fixture/public dataset.

Container work that publishes images, configures registries, runs services, adds production deployment automation, or changes VPS/systemd/Kubernetes behavior is out of scope.

## Artifact storage
Use the existing `BacktestEngine.export_report` artifacts and add the dataset manifest in the same run directory. Prefer a local path such as `artifacts/backtests/<run_id>/` or `reports/crypto/BTCUSDT/<run_id>/`.

Generated report directories should be ignored or otherwise protected from accidental commits unless a small deterministic fixture artifact is intentionally committed for tests. Do not inspect or print secrets while validating ignore behavior.

## Safety boundaries
The runner must be read-only with respect to exchange/private account state. It must not submit, cancel, modify, query, or reconcile live orders/positions. It must not require or read private API credentials.

The first experiment result is a research artifact only. It answers whether the data-to-report pipeline works, not whether the strategy is production-tradable.

## Follow-up path
After the BTCUSDT first artifact, later OpenSpec changes may add:
1. ETHUSDT and multiple crypto periods.
2. Top-N crypto batch runner.
3. Public downloader if omitted from this slice.
4. FX historical experiment runner with separate provider, spread/swap/session/symbol-mapping rules.
5. Optimization/walk-forward production approval gates.
