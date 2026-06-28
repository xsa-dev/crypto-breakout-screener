## ADDED Requirements

### Requirement: Heikin-Ashi transform is causal and derived from raw OHLCV
The runtime data layer SHALL compute Heikin-Ashi candles as deterministic derived features from raw OHLCV bars without replacing raw market data.

#### Scenario: Heikin-Ashi series is computed
- **WHEN** a historical run requests Heikin-Ashi features for a symbol/timeframe
- **THEN** the transform uses only raw bars up to each transformed bar timestamp
- **AND** records the transform seed rule and source raw data artifact.

#### Scenario: Economic accounting is performed
- **WHEN** fills, stops, targets, costs, PnL, equity, max drawdown, or profit factor are computed
- **THEN** the system uses raw OHLCV/accounting inputs
- **AND** does not use Heikin-Ashi open/high/low/close as executable market prices.
