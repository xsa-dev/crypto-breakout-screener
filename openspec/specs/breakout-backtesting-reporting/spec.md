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

### Requirement: BTCUSDT batch stress tests record realistic cost assumptions
The BTCUSDT batch runner SHALL support explicit stress-test cost assumptions for spread, slippage, commission, and funding, including notional commission and funding rates, and SHALL record those assumptions in deterministic batch artifacts.

#### Scenario: Stress run uses explicit notional costs
- **WHEN** the BTCUSDT batch runner is executed with non-zero notional commission or funding rates
- **THEN** each backtest window includes those costs in trade `total_cost` and `net_pnl`
- **AND** the batch summary JSON and CSV record the cost model settings used
- **AND** cached public market-data CSVs can be reused without network access when explicitly requested

#### Scenario: Tight ATR profile is stress-tested
- **WHEN** the `conservative-v1-m15-slope-positive-max-trades-8-atr-stop-0p01-target-2p0` profile is rerun over `2023q1..2024q4` under explicit stress cost assumptions
- **THEN** the output records per-quarter pass/fail status, blockers, trade count, net profit, max drawdown, profit factor, cost settings, and artifact paths
- **AND** the result is reported as research robustness evidence only, not production approval

#### Scenario: Ledger-level cost stress is used as negative robustness evidence
- **WHEN** exact quarterly reruns are too slow for an interactive loop
- **THEN** a separately labelled ledger-level stress artifact MAY preserve original entries/exits and subtract additional costs per realized trade
- **AND** the artifact SHALL NOT be described as an exact cost-dependent signal rerun

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

### Requirement: Backtests export failed-window bad-regime diagnostics
The backtest research reporting layer SHALL support deterministic diagnostics for failed windows of a selected research profile without changing default backtest behavior.

#### Scenario: Diagnostics enabled for failed quarterly windows
- **WHEN** diagnostics are enabled for `conservative-v1-m15-slope-positive-max-trades-8` over quarterly BTCUSDT 2023-2024 windows
- **THEN** failed-window diagnostic artifacts are written for windows that do not pass research thresholds
- **AND** each artifact includes profile name, window label, run id, and artifact schema metadata
- **AND** default runs without diagnostics do not require the additional artifacts

### Requirement: Bad-regime diagnostics report traceable bucket evidence
Bad-regime diagnostics SHALL aggregate failed-window evidence by deterministic dimensions derived from existing run artifacts and entry/context features.

#### Scenario: Bucket diagnostics are generated
- **WHEN** a failed window has entry feature snapshots and trades available
- **THEN** diagnostics include bucket-level trade count, net PnL, and available adverse/drawdown metrics
- **AND** buckets are stable across repeated runs on the same inputs
- **AND** bucket definitions are documented in the artifact or companion metadata

### Requirement: Worst drawdown runs are reportable
Failed-window diagnostics SHALL identify drawdown runs or worst-day clusters sufficient to explain whether a failure is broad-based or concentrated.

#### Scenario: Drawdown failure is concentrated
- **WHEN** a failed window breaches the max drawdown research threshold
- **THEN** diagnostics include the worst drawdown run or worst contributing day clusters where calculable
- **AND** output distinguishes profitable-but-drawdown-blocked windows from negative-expectancy windows

### Requirement: Backtests compare fixed volatility-regime filter profiles
The batch research runner SHALL support fixed, named volatility/no-trade regime filter profiles for BTCUSDT breakout research while preserving the existing baseline/reference profiles.

#### Scenario: Required volatility-regime profiles are available
- **WHEN** the quarterly BTCUSDT batch runner is invoked with each required volatility-regime profile
- **THEN** it runs the profile over the requested windows
- **AND** it records the profile name, settings, skip counts, artifact paths, and per-window blockers in summary CSV/JSON
- **AND** it keeps lifecycle gates, M15-slope feature filtering, and max-trades risk control identical to the approved reference profile except for the named regime filter condition

#### Scenario: Volatility-regime comparison completes
- **WHEN** all required volatility-regime profiles complete over quarterly 2023-2024 windows
- **THEN** the aggregate summary reports passed window count, failed window count, total trade count, total net profit, worst max drawdown, mean profit factor, hypothesis_supported, and hypothesis_not_supported for each profile
- **AND** the result is not represented as production approval

### Requirement: Regime-filter reporting is separate from gate and risk reporting
The batch summary SHALL expose volatility/no-trade regime filter reporting separately from lifecycle gates, feature filters, and risk controls.

#### Scenario: Summary CSV is written
- **WHEN** a volatility-regime profile is run
- **THEN** the summary CSV includes `regime_filter_profile`, `regime_filter_settings_json`, and `regime_filter_skip_counts_json`
- **AND** existing `gate_profile`, `feature_filter_profile`, and `risk_control_profile` fields remain populated according to their existing meanings

#### Scenario: Summary JSON is written
- **WHEN** a volatility-regime profile is run
- **THEN** the summary JSON includes the same regime-filter profile, settings, and skip-count data as the CSV

### Requirement: Backtests compare fixed breakout-confirmation profiles
The batch research runner SHALL support fixed, named breakout-confirmation comparison profiles for BTCUSDT public-data research.

#### Scenario: Confirmation profile is selected
- **WHEN** a batch run selects a supported confirmation profile
- **THEN** every window summary records `confirmation_filter_profile`
- **AND** every window summary records `confirmation_filter_settings_json`
- **AND** every window summary records `confirmation_filter_skip_counts_json`
- **AND** the batch JSON summary records the selected confirmation profile separately from gate, feature, and risk-control profiles.

#### Scenario: Confirmation profile is disabled
- **WHEN** the reference profile runs without confirmation filters
- **THEN** confirmation settings are empty or disabled
- **AND** confirmation skip counts are empty
- **AND** reference behavior is preserved.

### Requirement: Confirmation comparison reports research verdicts
Confirmation comparison artifacts SHALL make it possible to compare each fixed profile against the reference profile.

#### Scenario: Quarterly comparison is completed
- **WHEN** quarterly 2023-2024 BTCUSDT batches finish for confirmation profiles
- **THEN** the report states passed window count, failed window count, total trade count, total net profit, worst max drawdown, and `hypothesis_supported`
- **AND** remaining failed windows list blockers
- **AND** the report states whether confirmation improved, supported, or failed to support the breakout hypothesis.

### Requirement: Backtests export forward-path diagnostics
Backtest report export SHALL support deterministic forward-path diagnostics for completed trades. These diagnostics SHALL be computed after trade creation and SHALL NOT alter entry selection, sizing, exits, risk controls, or reported realized metrics.

#### Scenario: Forward-path diagnostics are enabled
- **WHEN** a completed backtest report is exported with forward-path diagnostics enabled
- **THEN** exported artifacts include a forward-path diagnostics CSV with one row per trade and fixed M15 horizons 1, 2, 4, 8, and 16 bars when available
- **AND** each row records entry identity, current realized outcome, forward close return, MFE, MAE, time-to-MFE, time-to-MAE, breakout-level return flag, below-entry crossing flag, and unavailable horizon reason when applicable
- **AND** enabling the diagnostics does not change the exported trade list or realized metrics

### Requirement: Holding-horizon summaries are diagnostic-only
Backtest report export SHALL support deterministic synthetic holding-horizon summaries for fixed M15 horizons. These summaries SHALL be labeled as diagnostics and SHALL remain separate from actual realized backtest results.

#### Scenario: Holding-horizon summary is exported
- **WHEN** forward-path diagnostics are enabled for a completed backtest
- **THEN** exported artifacts include a holding-horizon summary CSV grouped by fixed horizon
- **AND** the summary reports trade count, unavailable count, synthetic net PnL, average forward return, average MFE, average MAE, and positive-forward-return ratio
- **AND** the actual backtest metrics remain based on the implemented trade lifecycle, not the synthetic horizons

### Requirement: Batch summaries compare passed and failed forward-path behavior
The BTCUSDT batch runner SHALL support opt-in forward-path diagnostic summaries that compare passed and failed windows without changing the batch verdict logic.

#### Scenario: Forward-path batch diagnostics are enabled
- **WHEN** the BTCUSDT quarterly batch completes with forward-path diagnostics enabled
- **THEN** the batch artifact directory includes `forward-path-window-summary.csv` and `passed-vs-failed-forward-path-summary.csv`
- **AND** the batch summary JSON references those diagnostic artifact paths
- **AND** the batch verdict fields `technical_pass` and `hypothesis_supported` remain based on the existing research thresholds

### Requirement: Backtests export path-risk diagnostics
Backtest report export SHALL support deterministic path-risk diagnostics for already-produced trades when path-risk diagnostics are explicitly enabled.

#### Scenario: Path-risk diagnostics are exported as separate artifacts
- **GIVEN** a completed backtest report with trades and path-risk diagnostics enabled
- **WHEN** report artifacts are exported
- **THEN** the export includes a per-run `*-path-risk-diagnostics.csv`
- **AND** the export includes a per-run `*-path-risk-threshold-summary.csv`
- **AND** these artifacts are referenced in the report artifact paths
- **AND** actual realized metric artifacts remain unchanged.

#### Scenario: Batch path-risk summaries are exported separately
- **GIVEN** a batch run with path-risk diagnostics enabled
- **WHEN** the batch summary is written
- **THEN** the batch output includes `path-risk-window-summary.csv`
- **AND** the batch output includes `passed-vs-failed-path-risk-summary.csv`
- **AND** the batch summary JSON references those diagnostic artifact paths.

#### Scenario: Path-risk diagnostics preserve actual metrics
- **GIVEN** the same input data and strategy configuration
- **WHEN** path-risk diagnostics are enabled versus disabled
- **THEN** trade selection, actual realized metrics, and batch verdicts are identical
- **AND** path-risk feasibility labels are not reported as actual strategy results.

### Requirement: Path-risk diagnostics expose threshold ordering fields
Path-risk diagnostic artifacts SHALL include enough fields to compare favorable and adverse excursion ordering without implementing new exits.

#### Scenario: Threshold ordering fields are present
- **GIVEN** path-risk diagnostics for a trade with entry-time ATR available
- **WHEN** fixed favorable and adverse ATR thresholds are evaluated
- **THEN** the diagnostic row includes first favorable threshold hit, first adverse threshold hit, hit bar offsets, favorable-before-adverse labels, adverse-before-favorable labels, break-even reachability labels, break-even touch-after-reach labels, and fixed trailing giveback touch labels
- **AND** break-even reachability is defined as first reaching `+1.0 ATR` from entry inside the horizon
- **AND** trailing giveback labels use fixed `0.5 ATR` and `1.0 ATR` giveback levels below the maximum high observed after a favorable threshold was reached
- **AND** the labels are computed only from bars inside the configured horizon.

### Requirement: Backtests compare fixed research exit profiles
The BTCUSDT batch research runner SHALL support disabled-by-default, fixed, named exit-profile comparisons for path-risk, stop, break-even, trailing, holding, target-only, close-confirmed, delayed close-stop, partial, protected residual, large-target, realized drawdown-guard, large-target close-stop, occupancy-aware holding/target, exposure-scaled large-target, profit-lock trailing, and favorable-timeout exit hypotheses while preserving the existing reference behavior when no exit, drawdown-guard, occupancy, exposure-scaled, profit-lock trailing, or favorable-timeout profile is selected.

#### Scenario: Favorable-timeout profile is selected
- **WHEN** a supported favorable-timeout profile is selected by exact profile name
- **THEN** already-accepted long trades evaluate the configured favorable ATR threshold and timeout bar using existing post-entry M15 bars only
- **AND** a trade that has not reached the favorable threshold by the timeout bar exits at that bar close
- **AND** a trade that reaches the favorable threshold before or during the timeout bar continues to its configured target, close target, or fixed-hold fallback
- **AND** entry filters, research thresholds, cost model, data source, and default BTCUSDT behavior are unchanged
- **AND** the profile remains disabled unless selected explicitly.

### Requirement: Exit-profile batch summaries are auditable
BTCUSDT batch summaries SHALL expose exit-profile, delayed close-stop grace settings, occupancy gate, realized drawdown-guard, exposure-scaled, profit-lock trailing, and favorable-timeout comparison results separately from feature-filter, regime-filter, confirmation-filter, and cost dimensions.

#### Scenario: Favorable-timeout profile is evaluated against realistic costs
- **WHEN** a favorable-timeout profile is evaluated for the BTCUSDT quarterly `2023q1..2024q4` scorecard
- **THEN** success requires all eight quarters to pass after realistic costs with unchanged thresholds
- **AND** the summary records the target or close-target settings, favorable-timeout threshold and bar settings, cost settings, per-quarter metrics, blockers, and artifact paths
- **AND** no missing or skipped quarter is counted as a pass
- **AND** a below-`8/8` result is archived as falsified research evidence with no success notification.

### Requirement: Realistic-cost breakout profile search uses fixed eight-quarter gates
The BTCUSDT breakout research runner SHALL evaluate robust profile-search candidates against exactly the eight quarterly windows `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, and `2024q4`, using unchanged research thresholds: `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, and `require_no_feed_gaps=true`.

#### Scenario: Candidate scorecard is produced
- **WHEN** a robust breakout profile candidate is evaluated
- **THEN** the scorecard includes exactly `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, and `2024q4`
- **AND** the summary records the unchanged thresholds
- **AND** no missing or removed quarter can be counted as a pass
- **AND** each quarter records pass/fail status and blockers.

#### Scenario: Threshold weakening is attempted
- **WHEN** a candidate run lowers `min_trade_count`, `min_net_profit`, `min_profit_factor`, or `min_max_drawdown`, or disables `require_no_feed_gaps`
- **THEN** the run is marked non-acceptance research output
- **AND** it cannot produce a successful profile verdict.

### Requirement: Successful breakout profiles require realistic costs
The BTCUSDT breakout research verdict SHALL treat a profile as successful only when all eight required quarters pass after realistic costs, including notional `commission_rate=0.00055` per side, stressed spread/slippage, and conservative `funding_rate_per_bar > 0`.

#### Scenario: Profile passes after realistic costs
- **WHEN** a candidate profile passes all eight required quarters under realistic costs
- **THEN** the summary marks the candidate classification as `net_costs_supported`
- **AND** records `successful profile = 8/8 after realistic costs`
- **AND** records cost model settings, aggregate metrics, per-quarter metrics, blockers, and artifact paths.

#### Scenario: Profile passes baseline only
- **WHEN** a candidate profile passes all eight quarters under baseline or legacy costs
- **AND** the same candidate fails one or more required quarters under realistic costs
- **THEN** the summary marks baseline `8/8` as insufficient
- **AND** classifies the candidate as `falsified_realistic_costs`
- **AND** records the failed realistic-cost quarters and blockers as robustness evidence.

#### Scenario: Realistic cost settings are missing
- **WHEN** a candidate has no run or artifact proving `commission_rate=0.00055` per side, stressed spread/slippage, and `funding_rate_per_bar > 0`
- **THEN** the candidate cannot be classified as successful
- **AND** the blocker identifies the missing cost setting or missing artifact.

### Requirement: Robust profile artifacts are complete for every candidate
Every robust profile-search candidate SHALL produce deterministic artifacts that make baseline and realistic-cost verdicts auditable without manually reconstructing runs.

#### Scenario: Candidate artifacts are written
- **WHEN** a candidate evaluation completes or is falsified
- **THEN** its artifact directory includes `summary.json`
- **AND** includes `scorecard.csv`
- **AND** includes serialized `cost_model_settings` for baseline and realistic/stress runs
- **AND** records per-quarter pass/fail status, trade count, net profit, profit factor, max drawdown, feed gap status, blockers, and referenced run artifact paths.

#### Scenario: Candidate classification is reviewed
- **WHEN** a reviewer opens `summary.json`
- **THEN** it states one of `net_costs_supported`, `baseline_only_insufficient`, `falsified_realistic_costs`, `technical_blocked`, or `not_supported`
- **AND** the classification is traceable to the scorecard and cost settings.

### Requirement: Robust search moves away from cost-sensitive turnover
The robust profile search SHALL prioritize fixed, named profiles that reduce cost sensitivity versus the falsified tight ATR profile by limiting turnover and improving gross edge per trade.

#### Scenario: Candidate profile is defined
- **WHEN** a candidate profile is added to the search
- **THEN** its settings are named and serialized
- **AND** it documents how it attempts lower turnover, larger average trade, or stronger gross edge per trade through bounded controls such as cooldown, max trades, regime filters, or exit horizon
- **AND** it does not rely on broad unconstrained parameter search.

#### Scenario: High-turnover tight profile is used as reference
- **WHEN** a microscopic tight-stop, one-bar, or high-turnover profile is included
- **THEN** it is labelled as reference or negative robustness evidence unless it also passes the required realistic-cost `8/8` gate.

### Requirement: Occupancy large-target exit profiles are comparable
BTCUSDT batch summaries SHALL make fixed occupancy plus large-target exit candidates auditable against the required quarterly 2023-2024 research thresholds.

#### Scenario: Occupancy large-target candidate is selected
- **WHEN** the BTCUSDT quarterly batch runner is invoked with `conservative-v1-m15-slope-positive-max-trades-8-occupancy-target-4p0-hold-32` or `conservative-v1-m15-slope-positive-max-trades-8-occupancy-close-target-2p0-hold-32`
- **THEN** the batch uses the existing conservative M15 positive-slope and max-trades-8 gate settings
- **AND** it enables one-active-position occupancy by setting `block_overlapping_positions=true`
- **AND** it records deterministic exit profile settings for the configured target or close-target candidate
- **AND** it does not change default BTCUSDT behavior when those profile names are not selected.

#### Scenario: Occupancy large-target scorecard is produced
- **WHEN** an occupancy large-target candidate is evaluated under realistic costs
- **THEN** the scorecard uses unchanged thresholds `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, and `require_no_feed_gaps=true`
- **AND** the required quarterly windows remain exactly `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, and `2024q4` for any promoted full scorecard
- **AND** failed early-falsification quarters record blocker codes, metrics, and artifact paths rather than being counted as success.

#### Scenario: Occupancy large-target hypothesis reaches or fails success
- **WHEN** a candidate reaches all eight quarterly passes under realistic costs
- **THEN** `hypothesis_supported` is true only for that `8/8` candidate
- **AND** the final report lists all passed quarters, cost settings, metrics, and artifact paths
- **WHEN** no candidate reaches `8/8`
- **THEN** the change is archived as falsified/negative research evidence with remaining blockers and no success notification.

### Requirement: Large-target break-even exit profiles are compared as fixed BTCUSDT research candidates
The breakout batch runner SHALL support a bounded, disabled-by-default comparison of large-target plus break-even exit profiles for BTCUSDT research without changing default behavior, entry selection, costs, thresholds, or the quarterly scorecard definition.

#### Scenario: Candidate profile maps to deterministic exit settings
- **WHEN** `conservative-v1-m15-slope-positive-max-trades-8-target-3p0-breakeven-1p0-hold-32` is selected
- **THEN** the exit settings include `fixed_holding_bars=32`, `target_atr=3.0`, and `breakeven_after_atr=1.0`
- **AND** the risk-control profile remains `conservative-v1-m15-slope-positive-max-trades-8`
- **AND** the feature-filter profile remains `conservative-v1-m15-slope-positive`.

#### Scenario: Close-target candidate maps to deterministic exit settings
- **WHEN** `conservative-v1-m15-slope-positive-max-trades-8-close-target-2p0-breakeven-1p0-hold-32` is selected
- **THEN** the exit settings include `fixed_holding_bars=32`, `close_target_atr=2.0`, and `breakeven_after_atr=1.0`
- **AND** no entry/regime/confirmation filters are added by that profile.

#### Scenario: Quarterly comparison requires unchanged realistic-cost thresholds
- **WHEN** the comparison is evaluated
- **THEN** success requires all eight windows `2023q1`, `2023q2`, `2023q3`, `2023q4`, `2024q1`, `2024q2`, `2024q3`, and `2024q4` to pass
- **AND** costs remain `spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055`, and `funding_rate_per_bar=0.00001`
- **AND** thresholds remain `min_trade_count=1`, `min_net_profit=0.0`, `min_profit_factor=1.0`, `min_max_drawdown=-0.35`, and `require_no_feed_gaps=true`.

### Requirement: Breakout reports preserve evidence across universe sizes and cost tiers
Backtesting and portfolio reports SHALL preserve comparable evidence for one-coin, multi-coin, and promoted-universe runs with explicit cost-tier labeling.

#### Scenario: Scorecard is written
- **WHEN** a scorecard is generated for 1, 10, 50, 100, or fixed-universe symbols
- **THEN** the report records universe name, symbol count, symbols or symbol artifact path, windows, thresholds, costs, starting balance when applicable, exposure caps when applicable, status, blockers, and artifact paths.

#### Scenario: Cost assumptions differ
- **WHEN** comparing friction-light and realistic-cost runs
- **THEN** the report labels cost assumptions explicitly
- **AND** does not overwrite positive friction-light concept evidence with realistic-cost robustness failure.

#### Scenario: Documented screener coverage is reported
- **WHEN** implementation evidence is summarized
- **THEN** the report states which source-document algorithm blocks were active and which remained unimplemented or approximated.

### Requirement: Portfolio selection artifacts expose cost-feasibility skips
The shared-bankroll portfolio batch report SHALL expose opt-in selection profile decisions as deterministic artifacts separate from regime decisions and exposure-cap decisions.

#### Scenario: Selection profile is disabled
- **WHEN** a portfolio batch is run without a selection profile
- **THEN** selection settings and skip counts indicate no active selection gate
- **AND** trade acceptance, exposure cap behavior, shared equity accounting, and existing report fields are preserved.

#### Scenario: Cost-feasibility gate skips an entry
- **WHEN** `cost-feasible-v1` evaluates a long-enabled trade candidate whose entry-time friction ratio exceeds the configured maximum
- **THEN** the portfolio trade CSV retains the candidate row with `accepted=false`
- **AND** the blocker is `portfolio_selection_cost_feasibility`
- **AND** the candidate does not consume shared open exposure or affect net PnL/equity
- **AND** selection skip counts include the blocker.

#### Scenario: Selection profile summary is exported
- **WHEN** the portfolio summary JSON and scorecard CSV are written
- **THEN** they include the selection profile name, selection settings, and per-window skip counts or artifact references
- **AND** per-regime contribution rows include selected-off signals in skipped/blocked signal counts.

### Requirement: Portfolio scorecards expose quarter diagnostics
The shared-bankroll portfolio report SHALL write deterministic quarter diagnostics that explain passing, failed, blocked, and unknown windows without changing trading behavior.

#### Scenario: Quarter diagnostics are written
- **WHEN** a portfolio smoke or promoted scorecard is generated
- **THEN** the artifacts include per-quarter diagnostics for status, blockers, trade counts, skipped signal counts, net profit, profit factor, max drawdown, regime contribution, BTC/ETH context, market breadth, and relative strength summaries
- **AND** the summary JSON links to the diagnostics artifact.

#### Scenario: Passing and failing windows are compared
- **WHEN** the run contains at least two comparable window statuses
- **THEN** the diagnostics summary compares passing windows against failed or blocked windows
- **AND** reports the strongest observed differences and unavailable fields.

#### Scenario: Diagnostics remain non-causal
- **WHEN** diagnostics include realized outcome metrics
- **THEN** those metrics are labeled as outcome analysis
- **AND** they are not used as entry-time selection inputs by this change.

### Requirement: Reports disclose Heikin-Ashi feature usage
Backtesting and portfolio reports SHALL disclose when Heikin-Ashi was used as a derived feature view.

#### Scenario: Report includes Heikin-Ashi features
- **WHEN** scorecards, feature snapshots, or diagnostics include Heikin-Ashi fields
- **THEN** the report states that Heikin-Ashi was used only for feature extraction
- **AND** links or records the raw OHLCV accounting artifacts.

#### Scenario: Raw accounting artifact is missing
- **WHEN** a report uses Heikin-Ashi features but lacks raw-price accounting evidence
- **THEN** the run is marked blocked or incomplete for economic conclusions.
