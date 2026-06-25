## MODIFIED Requirements

### Requirement: Fast exit mode handles low breakouts
The system SHALL provide a `fast_exit_for_low_breakouts` option because low breakouts can accelerate on long liquidations/stops. When enabled for an explicitly identified short low-breakout scenario with positive planned quantity, local exit planning SHALL use an accelerated no-runner framework and record a machine-readable fast-exit reason. When disabled, when quantity is not positive, or when the setup is not a short low-breakout scenario, the baseline 30/50/20 framework SHALL remain unchanged.

#### Scenario: Fast exit is enabled
- **WHEN** a low-breakout short scenario reaches configured fast-exit conditions
- **THEN** the system exits faster than the default high-breakout runner framework
- **AND** the exit plan records `fast_exit_low_breakout`

#### Scenario: Fast exit falls back for non-low-breakout conditions
- **WHEN** `fast_exit_for_low_breakouts` is disabled or the setup is not an explicitly identified short low-breakout scenario
- **THEN** the system uses the baseline 30/50/20 exit framework
- **AND** the exit plan records a non-fast-exit reason
