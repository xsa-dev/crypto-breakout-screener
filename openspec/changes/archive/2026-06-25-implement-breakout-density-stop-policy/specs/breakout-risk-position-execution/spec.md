## MODIFIED Requirements

### Requirement: Density can define support and stop behavior
The system SHALL allow configured density/support to act as a trade-support premise and stop reference. When density is used as the support premise, local planning SHALL record the density reference, stop placement rule, and exit-on-density-eating rule. Density invalidation/eating against the trade SHALL produce a deterministic local reset/reduction decision with a machine-readable reason and remaining base position state.

#### Scenario: Density is used as support
- **WHEN** a setup uses density in the breakout direction as support
- **THEN** the trade plan records the density reference, stop placement rule, and exit-on-density-eating rule
- **AND** the stop reference is side-symmetric behind the density

#### Scenario: Density is eaten against the trade
- **WHEN** the density used as support is eaten or invalidated against the trade
- **THEN** the system exits or reduces the affected position according to configured risk policy
- **AND** the decision trace records `density_eaten` and remaining base position state
