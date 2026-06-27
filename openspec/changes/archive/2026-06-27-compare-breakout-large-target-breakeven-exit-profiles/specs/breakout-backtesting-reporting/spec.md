## ADDED Requirements

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
