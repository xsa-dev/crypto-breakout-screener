## 1. OpenSpec readiness
- [x] 1.1 Confirm the prior tight ATR exit profile change is archived/committed and there are no active OpenSpec changes.
  - Evidence: prior change is committed at `825550d`; `openspec list --json` shows only `stress-test-tight-atr-exit-realistic-costs` active.
- [x] 1.2 Record the baseline `8/8` artifact and metrics from `f7f80591545417ed`.
  - Evidence: `artifacts/exit-profile-comparison/crypto/BTCUSDT/f7f80591545417ed/summary.json` records `8/8`, total net profit `98652.00485712058`, total trades `3948`, mean profit factor `4.619254304970152`, worst max drawdown `-0.08265596607356647`, mean Sharpe `0.15545032470848924`.
- [x] 1.3 Validate this change strictly before implementation.
  - Evidence: `npx --yes @fission-ai/openspec@1.4.1 validate stress-test-tight-atr-exit-realistic-costs --strict --no-interactive` passed.

## 2. Implementation
- [x] 2.1 Add optional notional commission and funding fields to `BacktestCostModel` without changing defaults.
  - Evidence: added `commission_rate=0.0` and signed `funding_rate_per_bar=0.0`.
- [x] 2.2 Include notional commission/funding in trade `total_cost` and `net_pnl`.
  - Evidence: trade close now adds notional commission and funding on top of legacy explicit costs.
- [x] 2.3 Add batch runner cost parameters and pass them through to each quarterly run.
  - Evidence: batch runner accepts `--spread`, `--slippage`, `--commission-per-unit`, `--funding-per-bar`, `--commission-rate`, `--funding-rate-per-bar`, and `--reuse-market-data`.
- [x] 2.4 Record cost model settings in batch summary JSON/CSV.
  - Evidence: summary models and CSV include deterministic `cost_model_settings`.

## 3. Tests
- [x] 3.1 Add unit tests proving default cost behavior remains unchanged.
- [x] 3.2 Add unit tests for notional commission and funding cost calculations.
- [x] 3.3 Add batch tests proving cost settings are serialized and passed through.
  - Evidence: `env UV_CACHE_DIR=.uv-cache uv run pytest tests/test_breakout_backtesting_reporting.py tests/test_crypto_batch_experiment.py` passed `53` tests; targeted ruff passed.

## 4. Quarterly stress runs
- [x] 4.1 Run baseline compatibility stress for the tight ATR profile.
  - Evidence: ledger-level additive stress baseline preserved `8/8`, total net profit `98652.00485711829`, mean profit factor `4.619254304970152`, worst max drawdown `-0.08265596607356647`.
- [x] 4.2 Run realistic notional commission stress.
  - Evidence: ledger-level additive stress with `commission_rate=0.00055` per side failed `0/8`, total net profit `-738298.2622655531`, min profit factor `0.05108479336018737`.
- [x] 4.3 Run stressed spread/slippage plus notional commission stress.
  - Evidence: ledger-level additive stress with `spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055` failed `0/8`, total net profit `-767671.3822655531`.
- [x] 4.4 Run stressed spread/slippage plus notional commission and funding stress.
  - Evidence: ledger-level additive stress with `funding_rate_per_bar=0.00001` also failed `0/8`, total net profit `-775279.5151639532`.
- [x] 4.5 Record per-scenario scorecard, blockers, key metrics, and artifact paths.
  - Evidence: `artifacts/realistic-cost-stress-ledger/summary.json` and `artifacts/realistic-cost-stress-ledger/scorecard.csv`.
  - Note: exact cost-dependent quarterly rerun support was implemented, including cached market data, but an interactive exact baseline run was stopped after several minutes due backtest runtime. The stress verdict is ledger-level negative robustness evidence, not an exact signal rerun.

## 5. Final validation and closure
- [x] 5.1 Run strict OpenSpec validation and all-spec validation.
  - Evidence: strict change validation passed; `validate --all --strict` passed `11` items.
- [x] 5.2 Run relevant tests, lint, pyright, and `git diff --check`.
  - Evidence: targeted pytest passed `53`; `ruff check .` passed; `pyright` reported `0 errors`; `git diff --check` passed.
- [x] 5.3 Update tasks with final evidence and verdict.
  - Verdict: the found profile is not robust to realistic notional taker commission at the backtest position size. Ledger-level additive stress breaks `8/8` to `0/8` before additional spread/slippage/funding stress.
- [x] 5.4 Archive the change as robustness evidence or falsified robustness evidence.
  - Evidence: archived to `openspec/changes/archive/2026-06-27-stress-test-tight-atr-exit-realistic-costs` as falsified/negative robustness evidence.
- [x] 5.5 Commit scoped files if archived and repository state is safe.
  - Evidence: scoped commit includes code, tests, synced main spec, and archived OpenSpec change; unrelated `.dev/autonomous_dev.sh` remains unstaged.
