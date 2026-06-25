## 1. OpenSpec readiness
- [x] 1.1 Confirm the implementation scope is limited to first crypto historical experiments and does not include live trading, private account data, FX, optimization, or UI work.
- [x] 1.2 Validate this change strictly and validate all OpenSpec specs before source edits.
- [x] 1.3 Review artifact ignore policy so generated backtest/report directories cannot be accidentally committed as large local outputs.

## 2. Historical data loading and normalization
- [x] 2.1 Add a deterministic CSV historical OHLCV importer for BTCUSDT-compatible crypto bars.
- [x] 2.2 Normalize imported rows into the existing canonical `Bar` schema with UTC timestamps, symbol, timeframe, OHLCV, and source metadata.
- [x] 2.3 Implement deterministic deduplication/ordering and explicit out-of-order behavior.
- [x] 2.4 Validate OHLC invariants and report normalization warnings/errors.
- [x] 2.5 Detect timeframe gaps and expose them for the dataset manifest.
- [x] 2.6 Keep CSV/importer as the first required path; public downloader/provider remains deferred.

## 3. Dataset manifest and cost assumptions
- [x] 3.1 Add a dataset manifest model/writer with source, market, instrument type, symbol, timeframe, context timeframe availability, start/end, bar count, dataset hash, gaps, warnings, generated timestamp, and source metadata.
- [x] 3.2 Ensure manifest contents never include private credentials, authorization headers, `.env` values, private endpoint URLs, or account identifiers.
- [x] 3.3 Configure explicit BTCUSDT perpetual research cost assumptions: spread, slippage, commission/fee, and funding assumption or unavailable/deferred reason.
- [x] 3.4 Surface missing funding or other production-quality inputs as research limitations, not production approval.

## 4. Experiment runner and exports
- [x] 4.1 Add a simple `uv run`-friendly CLI/script entrypoint for the BTCUSDT crypto historical experiment.
- [x] 4.2 Accept symbol, timeframe, data source/path, optional date range, output directory, and cost-assumption inputs or defaults.
- [x] 4.3 Load/normalize data, compute dataset hash, construct `BacktestConfig`, run `BacktestEngine`, and export the existing report artifacts.
- [x] 4.4 Write the dataset manifest in the same local run artifact directory.
- [x] 4.5 Print a concise summary with run id, symbol, timeframe, bar count, dataset hash, config hash, trade count, net PnL/total metric, max drawdown, win rate, and artifact paths.
- [x] 4.6 Keep live broker/exchange execution, private API access, balances, positions, and account state unreachable from the runner.

## 5. Optional container execution wrapper
- [x] 5.1 Decide during implementation whether the first slice includes a container wrapper; omitted here, host `uv run` is authoritative and container parity remains follow-up scope.
- [x] 5.2 Not included; no container recipe/wrapper was added in this slice.
- [x] 5.3 Not applicable because no container mounts were introduced.
- [x] 5.4 Not applicable because no container wrapper was included; host fixture run was verified.

## 6. Tests
- [x] 6.1 Test CSV/public data parsing into canonical `Bar` records.
- [x] 6.2 Test UTC timestamp conversion, deterministic deduplication, ordering/out-of-order policy, OHLC validation, and gap manifest diagnostics.
- [x] 6.3 Test stable dataset hash for the same normalized dataset.
- [x] 6.4 Test runner/report determinism on a fixture BTCUSDT-like dataset.
- [x] 6.5 Test that private credentials are not required or read by the experiment path.
- [x] 6.6 Test artifact paths include the dataset manifest plus existing report exports.

## 7. Verification and review
- [x] 7.1 Run targeted tests for the crypto experiment importer/runner.
- [x] 7.2 Run `uv run pytest`.
- [x] 7.3 Run `uv run ruff check .`.
- [x] 7.4 Run `uv run pyright`.
- [x] 7.5 Run `npx --yes @fission-ai/openspec@1.4.1 validate implement-crypto-historical-experiment-runner --strict --no-interactive`.
- [x] 7.6 Run `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`.
- [x] 7.7 Run `git diff --check`.
- [x] 7.8 Run one real BTCUSDT fixture/public-data experiment command and record the produced report artifact path: `artifacts/backtests/crypto/BTCUSDT/3343d9d8d0955c5c/3343d9d8d0955c5c-dataset-manifest.json`.
- [x] 7.9 Not applicable because no container wrapper was included.
- [x] 7.10 Self-review that the output only proves reproducible data-to-report research, not production trading readiness.
