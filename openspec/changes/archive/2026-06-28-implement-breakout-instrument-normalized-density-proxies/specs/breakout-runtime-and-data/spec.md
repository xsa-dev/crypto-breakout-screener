## ADDED Requirements

### Requirement: Historical data reports density source availability
The runtime data layer SHALL distinguish real order book density from OHLCV-derived density proxies.

#### Scenario: Historical run lacks order book data
- **WHEN** a backtest or portfolio run has no historical DOM/L2 feed
- **THEN** reports label density source as `ohlcv_proxy` or `unavailable`
- **AND** do not require private/live exchange APIs to complete the historical run.

#### Scenario: Metadata is used for normalization
- **WHEN** tick size, min notional, precision, or provider symbol metadata affect normalized features
- **THEN** the metadata source is recorded in run artifacts.
