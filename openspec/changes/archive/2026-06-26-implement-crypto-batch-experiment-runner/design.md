# Design

## Scope
Add a local research batch runner on top of the already implemented BTCUSDT public-data experiment path. The batch runner must not create a second strategy/backtest implementation; it orchestrates repeated calls to the existing downloader and `run_crypto_experiment` flow, then aggregates the resulting metrics and artifact paths.

The first batch scope is intentionally narrow:
- market: crypto;
- venue/source: Bybit public unauthenticated kline API;
- symbol: BTCUSDT;
- instrument type: linear/perpetual;
- required downloaded timeframes per window: M15, H1, H4, D1;
- backtest execution input: M15 only;
- context datasets: H1/H4/D1 recorded in each manifest and batch summary;
- output: local per-run artifacts plus batch CSV/JSON summary;
- trading approval: research-only, never production approval.

## Windows
The runner should require explicit windows or use a named first-pass preset. A safe initial preset is quarterly-style windows such as:
- 2023-01-01T00:00:00Z -> 2023-04-01T00:00:00Z;
- 2023-04-01T00:00:00Z -> 2023-07-01T00:00:00Z;
- 2023-07-01T00:00:00Z -> 2023-10-01T00:00:00Z;
- 2023-10-01T00:00:00Z -> 2024-01-01T00:00:00Z;
- 2024-01-01T00:00:00Z -> 2024-04-01T00:00:00Z;
- 2024-04-01T00:00:00Z -> 2024-07-01T00:00:00Z;
- 2024-07-01T00:00:00Z -> 2024-10-01T00:00:00Z;
- 2024-10-01T00:00:00Z -> 2025-01-01T00:00:00Z.

Implementation may use shorter fixture/smoke windows in tests. Production-size quarterly downloads may be slow, so the CLI should allow the user to pass a smaller explicit window set for smoke runs.

## CLI shape
Exact flags can evolve during implementation, but the CLI should be `uv run` friendly. Examples:

`uv run python -m src.app.breakout.experiments.crypto_batch --preset quarterly-2023-2024 --market-data-dir artifacts/batch-market-data --output-dir artifacts/batch-backtests`

or an equivalent submode in the existing module:

`uv run python -m src.app.breakout.experiments.crypto_backtest --batch --windows-file windows.json --market-data-dir artifacts/batch-market-data --output-dir artifacts/batch-backtests`

The final command must be documented in tests/tasks and must not require credentials.

## Summary artifacts
Write batch artifacts under an ignored local directory, for example:

`artifacts/batch-backtests/crypto/BTCUSDT/<batch_id>/summary.csv`
`artifacts/batch-backtests/crypto/BTCUSDT/<batch_id>/summary.json`

Each window row should include:
- window id/label;
- start/end;
- status: `passed`, `failed`, or `blocked`;
- reason/blocker code when not passed;
- run id;
- dataset hash;
- config hash;
- bar count;
- trade count;
- net profit;
- max drawdown;
- profit factor;
- win rate;
- Sharpe;
- average trade/expectancy where available;
- feed gap count;
- context timeframe availability;
- downloaded CSV paths;
- manifest path;
- artifact directory.

The JSON summary should also include aggregate totals/means and a research verdict.

## Research verdict
The batch verdict is a research screen, not a production gate. It should be explicit and conservative:
- `technical_pass`: all windows completed with datasets, manifests, metrics, and no feed gaps;
- `hypothesis_supported`: all required windows pass configured research thresholds;
- `hypothesis_not_supported`: at least one required window fails, has no trades, missing metrics, feed gaps, or fails configured thresholds;
- `inconclusive`: reserved for explicit skipped real-network smoke in local verification, not for completed batch outputs.

Default research thresholds should be visible in the output and conservative enough for screening, for example: minimum trade count > 0, net profit > 0, profit factor > 1.0, max drawdown above a configured floor, no feed gaps. The thresholds are not production OOS gates and must not override the existing production OOS approval gate.

## Failure behavior
If a window fails to download or backtest, the batch runner should record a failed/blocked row with the error reason and continue or stop according to an explicit CLI flag/default. The default should be safe and reviewable; either fail-fast or continue-with-failed-row is acceptable if documented and tested. In all cases, partial failed windows must not be reported as passed.

## Safety
The batch runner inherits the public-data safety boundary:
- no `.env` reads;
- no `src.core.env` import;
- no API keys;
- no authorization headers;
- no private exchange/account endpoints;
- no live orders or account state.

Generated summaries and per-window manifests must not include secrets.
