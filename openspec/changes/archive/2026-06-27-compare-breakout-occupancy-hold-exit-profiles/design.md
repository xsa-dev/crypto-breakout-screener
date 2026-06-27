## Hypothesis

The primary failing mechanism is path/holding risk combined with unrealistic overlapping trade occupancy: profiles with `fixed_holding_bars > 1` currently update `last_exit_index`, but the research gate only blocks same-timestamp immediate re-entry. The engine can therefore continue accepting entries before the prior simulated position would have exited. This keeps trade count high and makes longer holding/target profiles a weak test of real position lifecycle.

The tested hypothesis is narrow: when a selected profile blocks entries until the previous simulated trade's exit index, longer holding/target profiles may reduce turnover and drawdown enough to improve the required quarterly scorecard.

## Fixed Candidate Profiles

Add only these fixed names:

1. `conservative-v1-m15-slope-positive-max-trades-8-occupancy-hold-8`
   - current lifecycle/feature/risk reference settings;
   - one-position occupancy gate enabled;
   - fixed hold 8 bars.
2. `conservative-v1-m15-slope-positive-max-trades-8-occupancy-target-2p0-hold-16`
   - occupancy gate enabled;
   - intrabar target `+2.0 ATR`;
   - fallback fixed hold 16 bars.
3. `conservative-v1-m15-slope-positive-max-trades-8-occupancy-target-3p0-hold-32`
   - occupancy gate enabled;
   - intrabar target `+3.0 ATR`;
   - fallback fixed hold 32 bars.

These profiles intentionally avoid close-stop/trailing/partial/protected residual variants because those were already falsified or degraded in archives. If all three fail, the change is falsified rather than expanding the grid.

## Implementation Plan

- Add `block_overlapping_positions: bool = False` to `BacktestResearchGateConfig`.
- In `_research_gate_reason`, skip a candidate when `block_overlapping_positions` is enabled and the current bar index is at or before `gate_state.last_exit_index`.
- Ensure the skip counter is machine-readable, e.g. `skipped_overlapping_position`.
- Map the three fixed profile names to the existing max-trades-8 + M15-slope-positive reference profile plus the new occupancy gate and exit settings.
- Keep baseline/reference behavior unchanged unless a profile explicitly enables occupancy.
- Add focused tests for profile parsing, skip behavior, unchanged default behavior, and summary serialization.

## Verification / Evidence

Before implementation, baseline reference evidence is:

- command/artifact source: archived scorecard `artifacts/realistic-cost-profile-search/conservative-v1-m15-slope-positive-max-trades-8/scorecard.csv`;
- score: `5/8` baseline/configured research thresholds;
- failed quarters: `2024q1`, `2024q2`, `2024q4`;
- blockers: net profit/profit factor/drawdown for `2024q1` and `2024q2`, drawdown for `2024q4`.

After implementation, run:

- `npx --yes @fission-ai/openspec@1.4.1 validate compare-breakout-occupancy-hold-exit-profiles --strict --no-interactive`
- targeted pytest for batch/profile/engine behavior;
- full `uv run pytest`, `uv run ruff check .`, `uv run pyright` when practical;
- quarterly BTCUSDT batch for the fixed profiles using cached public data where possible;
- realistic-cost profile evaluation when candidate artifacts are available.

A successful outcome requires all eight windows to pass unchanged thresholds. Anything below `8/8` is negative evidence and must be archived with scorecard/artifact paths and no success notification.
