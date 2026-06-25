# Design

## Scope
Implement a storage-local export completeness slice for `BacktestEngine.export_report`. The exporter already owns deterministic artifact creation and report path population, so the change is limited to `src/app/breakout/backtesting.py` and focused tests in `tests/test_breakout_backtesting_reporting.py`.

## Approach
1. Keep the full JSON report as the canonical artifact.
2. Add flat CSV artifacts for tabular diagnostics:
   - metrics (`metric,value`);
   - drawdown curve (`timestamp,drawdown`);
   - return distribution (`index,return`);
   - scenario breakdown (`scenario,count`);
   - score distribution (`bucket,count`);
   - false-breakout analysis (`metric,value`);
   - slippage report (`metric,value`).
3. Add a deterministic parameter snapshot JSON artifact because nested strategy config is not well represented as a flat CSV.
4. Return `BacktestReport` with all paths in a stable order so repeated exports of the same report are comparable.

## Data and Safety
- Artifacts are written only to the caller-supplied local directory.
- No secrets, `.env` values, network calls, broker calls, or runtime database access are introduced.
- No package dependencies are added.

## Verification
- TDD: add a failing test that asserts the additional artifact names, contents, and stable path order.
- Run targeted backtesting tests, full pytest, Ruff, Pyright, OpenSpec validation, duplicate spec/archive check, and git diff checks.
