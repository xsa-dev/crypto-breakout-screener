## ADDED Requirements

### Requirement: Reports disclose normalization and density proxy assumptions
Backtest and portfolio reports SHALL disclose how symbol-specific differences and density/support assumptions were handled.

#### Scenario: Scorecard is written
- **WHEN** a scorecard includes setup score or density/support features
- **THEN** it records whether thresholds were fixed normalized defaults, rolling percentiles, or calibration artifacts
- **AND** records density source as `dom`, `ohlcv_proxy`, or `unavailable`.

#### Scenario: Quarter diagnostics are written
- **WHEN** quarter diagnostics compare passing and failing windows
- **THEN** they include density proxy buckets and wick/body quality summaries when those fields are available.
