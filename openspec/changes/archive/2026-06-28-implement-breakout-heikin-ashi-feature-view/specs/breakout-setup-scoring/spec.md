## ADDED Requirements

### Requirement: Setup scoring can use Heikin-Ashi as a derived feature view
The breakout setup scoring system SHALL support opt-in Heikin-Ashi-derived features while preserving raw OHLCV for economic accounting.

#### Scenario: Named Heikin-Ashi profiles are available
- **WHEN** a historical runner or programmatic caller requests Heikin-Ashi-based behavior
- **THEN** the implementation exposes named profiles `heikin-ashi-trend-filter-v1`, `heikin-ashi-confirmation-v1`, and `heikin-ashi-exit-v1`
- **AND** reports active Heikin-Ashi profile names separately from raw feature, confirmation, and exit profile names.

#### Scenario: Heikin-Ashi features are enabled
- **WHEN** a setup score profile enables Heikin-Ashi features
- **THEN** feature snapshots include Heikin-Ashi body ratio, wick ratios, close location, color, color streak, trend persistence, compression, reversal hint, and failed-continuation hint where computable
- **AND** the score artifact labels them as derived features.

#### Scenario: Heikin-Ashi features are disabled
- **WHEN** a profile does not enable Heikin-Ashi
- **THEN** default raw-candle feature behavior is preserved.

#### Scenario: Heikin-Ashi does not replace density
- **WHEN** Heikin-Ashi features are used with no DOM/L2 data
- **THEN** density/support source remains `ohlcv_proxy` or `unavailable`
- **AND** the report does not claim real order book density was tested.
