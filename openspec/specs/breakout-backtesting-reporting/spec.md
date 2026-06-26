# breakout-backtesting-reporting Specification

## Purpose
Define deterministic local replay, validation analysis, and reproducible report artifacts for the breakout strategy before any live-trading approval.
## Requirements
### Requirement: Backtesting uses deterministic data and configuration hashes
The system SHALL produce deterministic backtest results for the same dataset hash and config hash, subject only to explicitly seeded randomness.

#### Scenario: Same run is repeated
- **WHEN** a backtest is rerun with identical dataset hash, config hash, and random seed
- **THEN** signals, trades, and metrics match the previous run

### Requirement: Backtests include realistic trading costs
The system SHALL model spread, commission, slippage, and funding/swap where applicable for the tested market.

#### Scenario: Cost model is missing
- **WHEN** a backtest is requested without required cost assumptions
- **THEN** the system blocks the run or marks it as non-acceptance research output

### Requirement: Validation separates IS, OOS, walk-forward, and Monte Carlo
The system SHALL support in-sample optimization, out-of-sample validation, walk-forward evaluation, and Monte Carlo robustness analysis.

#### Scenario: Optimization is requested
- **WHEN** parameters are optimized
- **THEN** optimization occurs only inside configured in-sample windows

#### Scenario: Walk-forward is run
- **WHEN** walk-forward validation is configured
- **THEN** the system reports train/validate/forward windows and pass ratio

#### Scenario: Monte Carlo is run
- **WHEN** Monte Carlo analysis is configured
- **THEN** the system can perturb trade order, slippage, trade skipping, or price path according to configured methods

### Requirement: Required metrics are reported
The system SHALL report CAGR, Sharpe Ratio, Max Drawdown, Win Rate, Expectancy, Average Trade, Avg Holding Time, and OOS Performance. It SHOULD also report Profit Factor and Exposure.

#### Scenario: Backtest report generated
- **WHEN** a backtest completes
- **THEN** the report includes all required metrics or explicit unavailable reasons

### Requirement: Reports include strategy diagnostics
The system SHALL produce reports with equity curve, drawdown chart, distribution of returns, trade list, scenario breakdown, score distribution, false breakout analysis, slippage report, parameter snapshot, and CSV/Parquet export.

#### Scenario: Report is exported
- **WHEN** the user exports a completed run report
- **THEN** exported artifacts include metrics, charts/series data, trade list, scenario/score diagnostics, and parameter snapshot

### Requirement: Production OOS thresholds are explicit gates
The system SHALL require project-specific numeric OOS/business-validity thresholds before any production full-auto GO. If thresholds are not configured, production full-auto approval is blocked even when backtest artifacts exist.

#### Scenario: OOS thresholds are missing
- **WHEN** a release candidate requests production full-auto approval without configured OOS thresholds
- **THEN** the review blocks production full-auto GO and records the missing thresholds

#### Scenario: OOS thresholds are configured
- **WHEN** OOS thresholds are configured for the target market and broker scope
- **THEN** acceptance review compares backtest/walk-forward/OOS outputs against those thresholds

### Requirement: Acceptance gates are measurable
The system SHALL require acceptance gates for functional coverage, determinism, risk limits, reconnect/idempotency, logs, test artifacts, documentation, operations, and OOS business validity.

#### Scenario: Acceptance review runs
- **WHEN** a release candidate is reviewed
- **THEN** the review can verify each acceptance category with concrete artifacts or explicit blockers

### Requirement: Backtests use the online information boundary
The backtest engine SHALL evaluate historical bars/ticks using only information available at each simulated timestamp and SHALL reuse the same level/setup/state/risk logic as online evaluation.

#### Scenario: Future data is unavailable during simulation
- **WHEN** a backtest evaluates a signal at bar N
- **THEN** the strategy cannot inspect bars after N except for explicitly delayed confirmation that would also be unavailable live

### Requirement: Reports are reproducible artifacts
The reporting layer SHALL produce deterministic report artifacts with config hash, dataset hash, parameter snapshot, trade list, scenario breakdown, score distribution, false-breakout analysis, slippage assumptions, equity, drawdown, and return distribution. Local report export SHALL materialize these diagnostics as separate deterministic artifacts, or record explicit unavailable reasons for unsupported optional formats.

#### Scenario: Report links to run metadata
- **WHEN** a backtest report is generated
- **THEN** it includes or references the backtest run id, config hash, dataset hash, time range, and exported artifact paths

#### Scenario: Diagnostic artifacts are exported
- **WHEN** a completed report is exported locally
- **THEN** artifact paths include the full report, trade list, equity curve, drawdown curve, return distribution, metrics, scenario breakdown, score distribution, false-breakout analysis, slippage report, and parameter snapshot
- **AND** repeated exports of the same report produce stable artifact names and content

### Requirement: Crypto experiment runner produces deterministic local backtest artifacts
The system SHALL provide a simple local runner or CLI/script entrypoint for the first BTCUSDT crypto historical experiment. The runner SHALL load normalized historical bars, compute dataset and configuration hashes, run the existing deterministic backtest engine, export report artifacts, write the dataset manifest, and print a concise summary. The runner SHALL also support a public download flow that writes BTCUSDT M15/H1/H4/D1 public historical OHLCV CSV input before running or preparing the existing experiment path.

#### Scenario: Runner executes BTCUSDT fixture or public-data experiment
- **WHEN** the user runs the crypto historical experiment command with BTCUSDT M15 fixture or public historical data
- **THEN** the command loads and normalizes the data
- **AND** computes a dataset hash
- **AND** constructs an explicit `BacktestConfig`
- **AND** runs `BacktestEngine`
- **AND** exports the report artifacts and dataset manifest to a local run directory
- **AND** prints run id, symbol, timeframe, bar count, dataset hash, config hash, trade count, net PnL or equivalent total metric, max drawdown, win rate, and artifact paths

#### Scenario: Repeated runner execution is reproducible
- **WHEN** the runner is executed twice with the same normalized dataset, cost assumptions, config, and random seed
- **THEN** the dataset hash, config hash, run id, and deterministic report artifacts match

#### Scenario: Runner downloads public BTCUSDT data before running
- **WHEN** the user runs the crypto experiment command in public-download mode with BTCUSDT, M15/H1/H4/D1, and explicit UTC start/end timestamps
- **THEN** the command downloads public unauthenticated OHLCV/kline data for all four required timeframes
- **AND** writes deterministic CSV inputs under an ignored local artifact/data directory
- **AND** runs or can immediately run the existing importer/backtest path against the M15 CSV while retaining H1/H4/D1 CSV paths as context datasets
- **AND** prints or records both the downloaded CSV paths and the report/manifest artifact path when a backtest is run

### Requirement: Crypto cost assumptions are explicit and research-scoped
The system SHALL require explicit non-zero crypto research cost assumptions for the first BTCUSDT perpetual/futures experiment, including spread, slippage, commission or fee, and funding assumption or an explicit unavailable/deferred reason.

#### Scenario: Crypto costs are configured
- **WHEN** the runner builds the backtest configuration for BTCUSDT perpetual/futures research
- **THEN** spread, slippage, and commission/fee assumptions are explicit and non-zero unless the run is marked non-acceptance research
- **AND** funding is either modeled explicitly or recorded as unavailable/deferred in report or manifest limitations

#### Scenario: Missing production-quality inputs are visible
- **WHEN** funding, higher-timeframe context, order-book density, or other production-quality inputs are unavailable for the first experiment
- **THEN** the report or manifest records explicit unavailable reasons
- **AND** the result is not represented as production full-auto or production OOS approval

### Requirement: Experiment artifacts include the dataset manifest
The report export path for crypto historical experiments SHALL include the existing deterministic backtest report artifacts and the dataset manifest in the same local artifact directory.

#### Scenario: Artifact directory is produced
- **WHEN** a crypto historical experiment completes
- **THEN** the artifact directory includes the full report JSON, trade list, equity curve, drawdown curve, return distribution, metrics, scenario breakdown, score distribution, false-breakout analysis, slippage report, parameter snapshot, and dataset manifest
- **AND** generated artifact directories are ignored or otherwise protected from accidental large local artifact commits unless a small fixture artifact is intentionally committed for tests

### Requirement: Production OOS approval gate is fail-closed
The system SHALL provide a deterministic local approval gate for production OOS/business-validity review that compares completed backtest metrics against explicit configured thresholds. The gate SHALL block approval when thresholds are absent, when a configured metric is missing or unavailable, or when a configured threshold is not met. Passing this local gate SHALL NOT enable live broker execution or production `full_auto` unless separately approved by deferred-scope gates.

#### Scenario: Thresholds are missing
- **WHEN** production OOS approval is evaluated without any configured numeric thresholds
- **THEN** the gate blocks approval
- **AND** the decision records `missing_oos_thresholds`

#### Scenario: Configured thresholds pass
- **WHEN** production OOS approval is evaluated with configured thresholds that are all satisfied by report metrics
- **THEN** the gate returns an approved local decision
- **AND** checked metrics are recorded for audit

#### Scenario: Configured metric is missing, unavailable, or fails
- **WHEN** a configured threshold references a missing metric, a metric with an unavailable reason, a `None` metric value, or a value that does not satisfy the threshold
- **THEN** the gate blocks approval
- **AND** the decision records a machine-readable blocker for that metric

### Requirement: Public download failures do not create completed reports
Public data download failures SHALL fail explicitly and SHALL NOT feed partial or malformed data into the backtest runner as a completed dataset.

#### Scenario: Provider returns an error, timeout, empty result, or malformed payload
- **WHEN** the public downloader cannot retrieve a valid non-empty BTCUSDT M15/H1/H4/D1 OHLCV datasets for the requested range
- **THEN** the command fails with an explicit error
- **AND** no completed report artifact is claimed for that failed download

#### Scenario: Provider pagination is rate-limited or retried
- **WHEN** the public provider temporarily rate-limits or fails a page request
- **THEN** the downloader may retry with bounded backoff
- **AND** it eventually succeeds deterministically or fails with a clear bounded-retry error

### Requirement: Crypto batch experiment runner summarizes multiple BTCUSDT windows
The system SHALL provide a local research batch runner for BTCUSDT crypto historical experiments that executes multiple explicit historical windows through the existing public-data download and M15 backtest path, then writes deterministic batch summary artifacts.

#### Scenario: Batch runner executes multiple windows
- **WHEN** the user runs the BTCUSDT batch experiment command with explicit windows or an approved preset
- **THEN** the runner evaluates each window using public unauthenticated BTCUSDT M15/H1/H4/D1 data
- **AND** runs the existing M15 crypto experiment path for each completed window
- **AND** writes per-window report artifacts and dataset manifests
- **AND** writes batch summary CSV and JSON artifacts under an ignored local artifact directory

#### Scenario: Batch summary contains per-window metrics
- **WHEN** a batch completes
- **THEN** each summary row includes window label, start, end, status, blocker or error reason when applicable, run id, dataset hash, config hash, bar count, trade count, net profit, max drawdown, profit factor, win rate, Sharpe ratio, average trade or expectancy, feed gap count, context timeframe availability, downloaded CSV paths, manifest path, and artifact directory

#### Scenario: Batch output is reproducible for equivalent inputs
- **WHEN** the batch runner is executed twice with the same windows, provider responses or fixture inputs, costs, config, and random seed
- **THEN** per-window dataset hashes, config hashes, run ids, deterministic report artifacts, and batch summary rows match except for explicitly generated-at metadata

### Requirement: Crypto batch research verdict is conservative and non-production
The batch runner SHALL produce a research-only verdict that distinguishes technical pipeline success from trading-hypothesis support. It SHALL NOT claim production readiness, OOS approval, full-auto readiness, or live trading permission.

#### Scenario: All windows satisfy research thresholds
- **WHEN** all required windows complete without feed gaps, include required metrics, have at least one trade, and satisfy configured research thresholds
- **THEN** the summary marks `technical_pass` true
- **AND** marks the hypothesis as supported for research screening only
- **AND** records the thresholds used

#### Scenario: Any required window fails or violates thresholds
- **WHEN** any required window fails to download, fails to backtest, has feed gaps, has no trades, lacks required metrics, or violates configured research thresholds
- **THEN** the summary marks the hypothesis as not supported
- **AND** records machine-readable blocker reasons per failed window
- **AND** does not mark the batch as production-approved

#### Scenario: Batch result is reviewed
- **WHEN** a user inspects the batch summary
- **THEN** the output clearly states that the result is a research screen only and not production OOS/full-auto approval

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

### Requirement: Backtests support research-only feature-filter profiles
The backtest runtime SHALL support disabled-by-default research feature filters that can be applied by explicit named profiles to compare entry-quality hypotheses. These filters SHALL use only entry-time feature snapshot values available before trade creation and SHALL NOT change baseline or conservative lifecycle-gate behavior unless a named feature-filter profile is selected.

#### Scenario: Feature filters are disabled by default
- **WHEN** a backtest runs without feature-filter configuration
- **THEN** trade selection and deterministic metrics remain equivalent to the same configuration before this change
- **AND** feature-filter skip counters are empty or zero

#### Scenario: M15 slope filter is applied
- **WHEN** a named research profile requires M15 EMA slope positive
- **THEN** a long entry is allowed only when the entry feature snapshot has `feature_ema_slope_atr > 0`
- **AND** entries with unavailable, zero, or negative slope are skipped with a deterministic reason

#### Scenario: H1 trend filter is applied
- **WHEN** a named research profile requires H1 long trend alignment
- **THEN** a long entry is allowed only when closed H1 context features report `feature_context_H1_trend_alignment == "long"`
- **AND** missing or unavailable H1 context skips the entry with an explicit deterministic reason

#### Scenario: Candle body cap is applied
- **WHEN** a named research profile configures a maximum candle body/range ratio
- **THEN** an entry is skipped when `feature_candle_body_range_ratio` is unavailable or greater than the configured cap

#### Scenario: Feature filters are research-only
- **WHEN** a feature-filter profile improves drawdown, profit factor, or passed-window count
- **THEN** the result remains a local research artifact
- **AND** it SHALL NOT claim production OOS approval, full-auto readiness, live-trading readiness, or broker execution permission

### Requirement: Crypto batch compares feature-filter profiles
The BTCUSDT crypto batch runner SHALL support named feature-filter comparison profiles that extend the existing `conservative-v1` lifecycle profile without changing `baseline` or `conservative-v1` semantics.

#### Scenario: Named feature-filter profiles are run
- **WHEN** the user runs the BTCUSDT quarterly batch with a named feature-filter profile
- **THEN** every window records the lifecycle gate profile, feature-filter profile, and serialized feature-filter settings
- **AND** every window records deterministic feature-filter skip counts or equivalent diagnostics
- **AND** summaries include trade count, net profit, max drawdown, profit factor, win rate, hypothesis verdict, and artifact paths

#### Scenario: Filter comparison is reviewed
- **WHEN** baseline, conservative-v1, and feature-filter quarterly summaries are available
- **THEN** the review can compare passed-window count, failed-window reasons, trade count, max drawdown, net profit, profit factor, and win rate without re-reading individual trade lists
- **AND** any recommended filter remains a follow-up research hypothesis unless a later OpenSpec change approves production use

### Requirement: Backtests support research-only drawdown risk-control profiles
The backtest runtime SHALL support disabled-by-default research risk-control profiles that can reduce drawdown concentration on top of explicit feature-filter profiles. These controls SHALL use only realized trade state and entry-time information available before a new trade is created.

#### Scenario: Risk controls are disabled by default
- **WHEN** a backtest runs without a drawdown risk-control profile
- **THEN** baseline, conservative lifecycle, and committed feature-filter profile behavior remains unchanged
- **AND** risk-control skip/pause counters are empty or zero

#### Scenario: Daily stop profile is applied
- **WHEN** a named research profile configures a stricter daily stop loss
- **THEN** entries after the stop is reached are skipped with a deterministic reason
- **AND** realized PnL is attributed to the trade exit UTC day

#### Scenario: Loss-cooldown profile is applied
- **WHEN** a named research profile configures a longer cooldown after loss
- **THEN** entries after realized losing trades are skipped until the configured cooldown has elapsed
- **AND** skip counts identify the cooldown reason

### Requirement: Batch summaries compare drawdown risk-control profiles
BTCUSDT batch summaries SHALL make drawdown risk-control comparisons auditable across the quarterly 2023-2024 windows.

#### Scenario: Risk-control profile batch completes
- **WHEN** a quarterly batch runs with a named drawdown risk-control profile
- **THEN** every summary window records the profile name, serialized settings, skip/pause counts, and artifact paths
- **AND** the aggregate summary records trade count, net profit, worst max drawdown, profit factor, passed-window count, failed-window count, blockers, and hypothesis verdict

#### Scenario: Worst-day evidence is reviewed
- **WHEN** a risk-control profile still fails one or more windows
- **THEN** the summary or referenced artifacts identify worst-day attribution for the failed windows
- **AND** the review can compare whether failures are broad-window degradation or concentrated worst-day drawdown
