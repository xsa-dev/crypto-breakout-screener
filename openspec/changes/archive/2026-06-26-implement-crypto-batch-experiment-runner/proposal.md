# implement-crypto-batch-experiment-runner

## Why
A single one-day BTCUSDT smoke run proves that public data download and local report generation work, but it does not prove or reject the trading hypothesis. To evaluate whether the breakout strategy has persistent positive expectancy, the project needs a batch research runner that executes the existing BTCUSDT public-data experiment across multiple fixed historical windows and writes one aggregated summary table with per-window metrics and a research-only verdict.

## What Changes
- Add a BTCUSDT crypto batch experiment mode that runs multiple explicit historical windows through the existing public downloader and M15 backtest runner.
- Default to a small, reviewable set of quarterly-style windows suitable for first hypothesis screening, while allowing a user-provided windows file or CLI windows list.
- For each window, download or reuse public Bybit M15/H1/H4/D1 datasets, run the existing BTCUSDT M15 experiment, and collect report/manifest paths.
- Produce a deterministic batch summary artifact containing period, run id, dataset hash, config hash, bar count, trade count, net profit, max drawdown, profit factor, win rate, Sharpe, feed gaps, context dataset status, and artifact paths.
- Produce a research verdict per window and an aggregate verdict that clearly distinguishes technical/data-pipeline success from trading-hypothesis support.

## Non-Goals
- No new trading strategy logic, parameter optimization, OOS approval, walk-forward optimization, Monte Carlo, or production full-auto approval.
- No live trading, private exchange API, API keys, account state, order placement, broker reconciliation, or position sync.
- No FX/XAUUSD/EURUSD, ETHUSDT, top-N symbols, multi-market batch, UI/dashboard, database persistence, scheduler, container/deployment work, or cloud execution.
- No change to the current M15-only backtest consumption: H1/H4/D1 remain downloaded context datasets until a separate context-aware strategy change.

## Acceptance Criteria
- A user can run one `uv run` command to evaluate BTCUSDT over multiple explicit windows using public unauthenticated Bybit data for M15/H1/H4/D1.
- Each window produces the existing per-run artifacts and dataset manifest, and the batch summary records their paths.
- The batch summary is written under an ignored artifact directory as CSV and JSON, with one row per window and an aggregate section.
- The summary includes enough metrics to judge the first hypothesis screen: trades, net PnL, max drawdown, profit factor, win rate, Sharpe, average trade/expectancy where available, feed gaps, and context timeframe availability.
- The batch verdict is fail-closed/research-only: it SHALL NOT claim production readiness and SHALL mark the hypothesis as not supported if any required window fails, has feed gaps, lacks trades, lacks required metrics, or violates configured research thresholds.
- Tests cover mocked multi-window execution without network, partial-window failure behavior, summary determinism, threshold/verdict logic, secret safety, and integration with existing single-run artifacts.
- Verification includes targeted tests, full pytest, Ruff, Pyright, strict OpenSpec validation, `git diff --check`, and one real or explicitly skipped public BTCUSDT batch smoke.
