# Design

## Evidence from current batch
The BTCUSDT quarterly batch produced a technical pass but hypothesis rejection. Artifact analysis showed:

- trades per quarter are almost equal to M15 bar count (`trades/bar ~= 0.99`);
- 100% of sampled trades have `holding_bars=1`;
- around 99.8%-100% of trades re-enter exactly at the previous trade exit timestamp;
- daily trade count averages about 95-96, matching the maximum M15 bars per day;
- all trades are long-only;
- bad quarters are driven by many repeated one-bar losses and large losing days rather than data gaps.

Relevant implementation points:
- `BacktestEngine.run()` evaluates every closed bar independently.
- `_close_next_bar_trade()` forces exit on `next_bar` and `holding_bars=1`.
- `_evaluate_closed_bar()` constructs a fresh `RiskState()` for every bar.
- The backtest does not maintain open-position memory, cooldown state, daily realized PnL state, or per-level/regime trade memory.

## Implementation approach

### Diagnostics first
Add deterministic diagnostics to `BacktestEngine.export_report()` or helper functions called by it. Keep existing artifact names stable and add new CSV artifacts rather than changing existing CSV schemas unless necessary.

Proposed new artifacts:
- `<run_id>-daily-summary.csv`
- `<run_id>-weekly-summary.csv`
- `<run_id>-lifecycle-diagnostics.csv`
- `<run_id>-score-bucket-pnl.csv`

The full report JSON may also include these diagnostic summaries if this fits current model conventions, but CSV artifacts are the required output.

### Diagnostic fields
Daily/weekly summaries should include:
- period key (`YYYY-MM-DD` or ISO week);
- trade_count;
- net_pnl;
- gross_pnl;
- total_cost;
- win_count;
- loss_count;
- win_rate;
- max_loss_streak_inside_period when computable.

Lifecycle diagnostics should include:
- total_trades;
- total_bars when available;
- trades_per_bar;
- holding_bars_min/max/average;
- holding_bars_distribution;
- immediate_reentry_count;
- immediate_reentry_ratio;
- same_day_max_trades;
- average_daily_trades;
- max_losing_streak;
- side_distribution;
- entry_score_min/max/average;
- repeated_level_trade_count when level metadata exists.

Score-bucket diagnostics should include:
- score;
- trade_count;
- net_pnl;
- average_trade;
- win_rate.

### Research gates
Add a small config model for local backtest research gates. It should default to disabled/no-op so existing deterministic tests and reports do not change unless gates are explicitly configured.

Candidate fields:
- `min_entry_score: int | None = None`
- `cooldown_bars_after_trade: int = 0`
- `cooldown_bars_after_loss: int = 0`
- `block_immediate_reentry: bool = False`
- `max_trades_per_day: int | None = None`
- `daily_stop_loss: float | None = None`

Gate behavior:
- evaluated before creating/accepting a new trade;
- deterministic and based only on simulated information available up to current bar;
- rejected/skipped entries are counted in diagnostics but not exported as trades;
- gate settings are included in the report parameter snapshot/config hash.

### State needed by gates
Backtest replay should maintain minimal local research gate state:
- last exit timestamp;
- last trade index;
- last trade net PnL;
- current UTC day;
- trades taken per day;
- realized PnL per day;
- current cooldown-until index.

This is not a full live broker state and must not pretend to be production execution. It is a deterministic local research filter.

### Batch comparison
Extend the crypto batch runner to support named profiles or explicit gate options sufficient to rerun:
- baseline/current profile;
- conservative gated profile.

At minimum, summary artifacts must record which gate profile/config was used and include trade_count/max_drawdown/net_profit/PF/win_rate per window. It is acceptable to run two separate batch commands and compare their `summary.csv` outputs if the implementation keeps profile support minimal.

### Safety
No private data, no `.env`, no broker state, no live execution. Generated diagnostics stay under ignored `artifacts/` directories.

### Test strategy
- Unit tests for diagnostics with small synthetic trade lists.
- Regression test that a one-bar trade sequence reports immediate re-entry ratio correctly.
- Tests that default gates are no-op relative to current behavior.
- Tests for each gate type using deterministic fixture bars:
  - min score filters low-score entries;
  - cooldown after trade reduces immediate next-bar entries;
  - cooldown after loss triggers only after losing trade;
  - max trades/day blocks after threshold;
  - daily stop-loss blocks after realized PnL crosses threshold.
- Batch test that summary includes gate/profile metadata.

## Risks
- Gates can hide lifecycle flaws if treated as strategy proof. Output must remain research-only.
- Overly strict gates may reduce trades but also destroy signal; repeat batch comparison is required.
- Full position lifecycle with stops/targets/partial exits is still separate work.
