## ADDED Requirements

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
