## ADDED Requirements
### Requirement: Backtest reports export entry feature diagnostics
Backtest report export SHALL include deterministic entry-time feature diagnostics for local research analysis. Feature calculation SHALL use only data available at or before the simulated entry bar and SHALL NOT affect default trade selection unless a separate approved change adds filters.

#### Scenario: Entry feature snapshots are exported
- **WHEN** a completed backtest report is exported locally
- **THEN** exported artifacts include an entry feature snapshot CSV with one row per exported trade
- **AND** each row includes trade id, symbol, side, entry time, entry index when available, setup score, selected M15 technical features, lifecycle state features, optional context feature availability, and outcome columns for offline grouping
- **AND** feature values are deterministic for the same report inputs

#### Scenario: Feature calculation avoids lookahead
- **WHEN** entry features are computed for a simulated trade
- **THEN** M15 features use only closed M15 bars at or before the entry timestamp
- **AND** H1/H4/D1 context features, when supplied, use only closed context bars with timestamps at or before the entry timestamp
- **AND** feature calculation does not read future bars, exit price, future PnL, or post-entry drawdown

#### Scenario: Feature bucket diagnostics are exported
- **WHEN** a completed report contains entry feature snapshots and trades
- **THEN** exported artifacts include feature-bucket PnL, regime-bucket summary, and worst-day attribution CSVs
- **AND** those artifacts include trade count, net PnL, average trade, win rate, and profit factor where computable or explicit unavailable values where not computable

#### Scenario: Missing context is explicit
- **WHEN** H1/H4/D1 context CSV paths are not supplied or a context timeframe has no closed bar at or before entry time
- **THEN** entry feature snapshots and bucket artifacts are still exported
- **AND** context fields record unavailable markers or reasons instead of failing the M15 backtest

### Requirement: Feature diagnostics preserve lifecycle research boundaries
Feature diagnostics SHALL remain local, deterministic, research-only diagnostics and SHALL NOT add ML training, automatically selected thresholds, production approvals, or live trading behavior.

#### Scenario: Diagnostics do not change baseline strategy
- **WHEN** a backtest runs with feature diagnostics enabled and no separate feature filters configured
- **THEN** trade selection, run id inputs, and deterministic report metrics remain equivalent to the same backtest without feature-based filters except for added diagnostic artifacts and metadata

#### Scenario: Diagnostics identify follow-up hypotheses only
- **WHEN** feature buckets identify profitable or low-drawdown regimes
- **THEN** the output may recommend candidate follow-up filters or ML research
- **AND** it SHALL NOT claim production OOS approval, full-auto readiness, live trading readiness, or broker execution permission
