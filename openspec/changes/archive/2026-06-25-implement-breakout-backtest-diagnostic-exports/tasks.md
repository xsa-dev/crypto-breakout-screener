## 1. OpenSpec readiness
- [x] 1.1 Confirm scope maps to existing `breakout-backtesting-reporting` capability and does not create a new capability name.
- [x] 1.2 Validate the change and all specs before source edits.

## 2. Implementation
- [x] 2.1 Add a failing focused test for deterministic diagnostic export artifacts.
- [x] 2.2 Extend `BacktestEngine.export_report` with metrics, drawdown, returns, scenario, score, false-breakout, slippage, and parameter snapshot artifacts.
- [x] 2.3 Preserve existing report JSON, trades CSV, equity CSV, deterministic ordering, and no live/cloud side effects.

## 3. Verification and landing
- [x] 3.1 Run targeted backtesting tests.
- [x] 3.2 Run full project tests.
- [x] 3.3 Run Ruff, Pyright, OpenSpec validation, duplicate spec/archive check, and git diff checks.
- [x] 3.4 Self-review the diff against the spec and acceptance criteria.
- [x] 3.5 Mark tasks complete, archive the change, re-run validation, verify no duplicate specs, and create one local commit.
