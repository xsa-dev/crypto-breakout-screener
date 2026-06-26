# breakout-backtesting-reporting Specification Delta

## ADDED Requirements
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
