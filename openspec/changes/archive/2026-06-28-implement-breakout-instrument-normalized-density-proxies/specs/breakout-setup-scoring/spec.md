## ADDED Requirements

### Requirement: Breakout setup scoring uses instrument-normalized features
The breakout setup scoring system SHALL use normalized, data-driven features instead of hardcoded per-symbol strategy thresholds.

#### Scenario: Candidate features are computed for different symbols
- **WHEN** setup features are computed for symbols with different price scales, volatility, and liquidity
- **THEN** price distance, breakout buffer, consolidation, volume, volatility, and wick/body quality are expressed as ATR multiples, rolling percentiles, relative volume, candle ratios, or documented metadata-derived values
- **AND** no manual symbol-specific strategy threshold is required.

#### Scenario: Per-symbol calibration is used
- **WHEN** per-symbol calibration is needed
- **THEN** it is computed only from the declared in-sample or causal rolling window
- **AND** the calibration artifact path and window are recorded
- **AND** out-of-sample or future bars are not used.

### Requirement: Density/support can be proxied from OHLCV when DOM is unavailable
The setup scoring system SHALL support an explicit OHLCV-derived proxy for density/support when historical order book data is unavailable.

#### Scenario: DOM/L2 data is unavailable
- **WHEN** density/support is needed and no historical DOM/L2 data is available
- **THEN** the feature snapshot labels density source as `ohlcv_proxy`
- **AND** computes volume near level, relative volume expansion, candle body dominance, wick rejection, close-location quality, and absorption/hold proxy where inputs are available.

#### Scenario: Density proxy is used in score
- **WHEN** the setup score uses OHLCV density proxy components
- **THEN** the score artifact exposes component values and missing-feature blockers
- **AND** does not claim real order book density was tested.
