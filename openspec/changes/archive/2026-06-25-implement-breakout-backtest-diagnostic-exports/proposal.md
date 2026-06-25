# implement-breakout-backtest-diagnostic-exports

## Why
The approved `breakout-backtesting-reporting` capability requires exported backtest artifacts to include metrics, charts/series data, trade list, scenario/score diagnostics, and parameter snapshot. The current local exporter writes the full JSON report plus trades and equity CSVs, but it does not provide separate deterministic diagnostic CSV artifacts for drawdown, returns, scenario breakdown, score distribution, false-breakout analysis, slippage assumptions, or parameter snapshot inspection.

## What Changes
- Extend the deterministic local backtest exporter to write separate CSV/JSON diagnostic artifacts in addition to the existing report JSON, trades CSV, and equity CSV.
- Include artifact paths for metrics, drawdown curve, return distribution, scenario breakdown, score distribution, false-breakout analysis, slippage report, and parameter snapshot.
- Preserve deterministic filenames/content for identical reports and keep the implementation storage-local with no live broker, cloud, or network side effects.

## Non-Goals
- No new live broker/exchange/terminal adapter.
- No production full-auto approval or cloud delivery.
- No Parquet dependency or package/lockfile change.
- No new permanent OpenSpec capability name; this is a narrow delta under `breakout-backtesting-reporting`.

## Acceptance Criteria
- Exported artifact paths include deterministic report, trade list, equity curve, drawdown curve, returns, metrics, scenario breakdown, score distribution, false-breakout analysis, slippage report, and parameter snapshot files.
- The diagnostic files contain the corresponding report payloads and are stable for repeated exports of the same report.
- Existing deterministic backtesting behavior remains unchanged.
- OpenSpec validation, tests, lint, typecheck, and git diff checks pass.
