## ADDED Requirements
### Requirement: Backtest reports include lifecycle overtrading diagnostics
Backtest report export SHALL include deterministic lifecycle diagnostics that make excessive trade frequency, one-bar holding, and immediate re-entry visible without requiring manual trade-list analysis.

#### Scenario: Lifecycle diagnostics are exported
- **WHEN** a completed backtest report is exported locally
- **THEN** exported artifacts include lifecycle diagnostics with total trades, total bars when available, trades per bar, holding-period distribution, immediate re-entry count and ratio, side distribution, average/max daily trades, and max losing streak
- **AND** the diagnostics are deterministic for the same report inputs

#### Scenario: Day and week summaries are exported
- **WHEN** a completed backtest report is exported locally
- **THEN** exported artifacts include daily and weekly summary CSVs with period key, trade count, net PnL, gross PnL, total cost, win count, loss count, and win rate

#### Scenario: Score bucket PnL is exported
- **WHEN** a completed backtest report contains scored trades
- **THEN** exported artifacts include score-bucket diagnostics with score, trade count, net PnL, average trade, and win rate

### Requirement: Research entry gates are deterministic and disabled by default
The backtest configuration SHALL support local research entry gates that can be used to diagnose and reduce overtrading. These gates SHALL be disabled by default so existing baseline behavior is preserved unless explicitly configured.

#### Scenario: Default gates preserve baseline behavior
- **WHEN** a backtest runs without configured research gates
- **THEN** trade selection and deterministic report outputs remain equivalent to the existing baseline behavior except for additional diagnostic artifacts

#### Scenario: Configured gates skip entries deterministically
- **WHEN** research gates are configured for minimum score, cooldown after trade, cooldown after loss, immediate re-entry blocking, max trades per day, or daily stop loss
- **THEN** the backtest evaluates those gates using only information available up to the simulated bar
- **AND** skipped entries are not exported as trades
- **AND** gate settings and skip counts are recorded in report parameters or diagnostics

#### Scenario: Gates remain research-only
- **WHEN** a gated backtest improves trade count or drawdown
- **THEN** the output remains a local research artifact
- **AND** it SHALL NOT claim production OOS approval, full-auto readiness, live trading readiness, or broker execution permission

### Requirement: Crypto batch can compare baseline and gated research profiles
The BTCUSDT crypto batch runner SHALL support running or summarizing a conservative gated research profile in addition to the baseline profile so lifecycle-gate effects can be compared across the same historical windows.

#### Scenario: Gated batch is run
- **WHEN** the user runs the BTCUSDT batch with a gated research profile or explicit gate options
- **THEN** every window records the gate profile or gate settings used
- **AND** the summary includes trade count, net profit, max drawdown, profit factor, win rate, hypothesis verdict, and artifact paths for the gated run

#### Scenario: Baseline and gated summaries are compared
- **WHEN** baseline and gated quarterly summaries are available
- **THEN** the review can compare trade count, max drawdown, net profit, profit factor, and hypothesis verdict without re-reading individual trade lists
