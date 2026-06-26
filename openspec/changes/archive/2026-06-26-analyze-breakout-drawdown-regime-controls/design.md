# Design

## Goal
Investigate the residual drawdown failures of the best current breakout research profile and compare a small set of deterministic risk-control profiles.

Base candidate:

`conservative-v1-m15-slope-positive`

Known failed windows from the committed feature-filter comparison:

- 2023q2: profitable but drawdown failed.
- 2024q1: net/PF/drawdown failed.
- 2024q2: near-flat but drawdown failed.
- 2024q4: profitable but drawdown failed.

The implementation should answer:

1. Are failures driven by a few worst days or broad degradation?
2. Do stricter daily/session risk controls improve passed-window count?
3. Do loss-streak or post-loss pauses reduce drawdown without destroying net profit?
4. Which controls remain robust across all eight quarters?

## Proposed Implementation

### 1. Risk-control configuration
Add disabled-by-default research risk controls to backtest config, separate from feature filters and lifecycle gates.

Potential fields:

- `daily_stop_loss`: may reuse existing lifecycle gate setting through named profiles, but stricter values should be explicit in profile settings.
- `max_trades_per_day`: may reuse existing lifecycle gate setting through named profiles, but stricter values should be explicit.
- `cooldown_bars_after_loss`: may reuse existing lifecycle gate setting through named profiles.
- `loss_streak_day_pause_count`: optional count of realized losing trades in the current UTC day that triggers a pause.
- `loss_streak_day_pause_bars`: optional pause duration after the loss-streak trigger.
- `post_large_loss_pause_bars`: optional pause after a realized loss larger than an explicit threshold.
- `large_loss_threshold`: optional absolute net-loss threshold for post-large-loss pause.

Only implement controls required by the approved profile set. Keep all controls disabled unless explicitly selected.

### 2. Named profiles
Compare a small fixed set. Do not implement arbitrary optimization.

Required profiles:

- `conservative-v1-m15-slope-positive`
  - current best reference.
- `conservative-v1-m15-slope-positive-daily-stop-3000`
  - same as best reference, stricter daily stop loss.
- `conservative-v1-m15-slope-positive-daily-stop-2000`
  - stricter daily stop loss stress test.
- `conservative-v1-m15-slope-positive-max-trades-8`
  - lower daily trade cap.
- `conservative-v1-m15-slope-positive-loss-cooldown-12`
  - longer cooldown after losing trades.

Optional if the implementation remains small and tests are clear:

- `conservative-v1-m15-slope-positive-two-loss-day-pause`
  - pause after two realized losses in the same UTC day.

### 3. Worst-window/worst-day reporting
For the best reference and every risk-control profile, summaries should identify:

- failed-window blockers;
- worst day by net PnL;
- worst day by realized drawdown contribution if available;
- trades on worst day;
- feature/regime buckets for worst-day entries when existing feature artifacts make them available;
- risk-control skip/pause counts per window.

Prefer deriving this from existing artifacts:

- `<run_id>-worst-day-attribution.csv`;
- `<run_id>-regime-bucket-summary.csv`;
- `<run_id>-feature-bucket-pnl.csv`;
- `<run_id>-parameters.json`.

Avoid duplicating large trade lists into batch summary JSON.

### 4. Batch summary output
Extend research summaries so each window records:

- `risk_control_profile` or equivalent profile name;
- serialized risk-control settings;
- deterministic risk-control skip/pause counters;
- worst-day artifact paths or compact worst-day summary fields.

The summary must remain deterministic and CSV/JSON readable.

### 5. Public-data boundary
Use only BTCUSDT public Bybit data already supported by the project:

- M15 execution;
- H1/H4/D1 context;
- public unauthenticated market data or existing CSV artifacts;
- no private API or live execution.

## Acceptance Criteria
- Default baseline/conservative/feature-filter behavior remains unchanged when no new risk-control profile is selected.
- Every named profile has deterministic settings recorded in summary CSV/JSON.
- Risk-control skip/pause counts are auditable per window.
- Quarterly 2023-2024 comparison runs complete for all required profiles.
- The report explicitly states whether the hypothesis passes; if not, it identifies remaining failed windows and blockers.
- Full verification passes: pytest, ruff, pyright, OpenSpec strict validation, and `git diff --check`.

## Risks
- Too many parameter variants can become optimization by hand. Keep the profile count fixed and small.
- A stricter daily stop may improve drawdown but reduce profit factor/trade count. The final review must compare all thresholds, not only drawdown.
- Loss-streak pauses must use realized PnL only after trade exit, never future PnL.
- Cross-midnight trades must attribute realized PnL and loss streaks to the exit UTC day, matching the existing daily stop-loss correction.
