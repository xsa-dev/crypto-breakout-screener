## MODIFIED Requirements

### Requirement: Context filters can block technically valid breakouts
The system SHALL apply configured market-direction and “поводырь” context filters such as EMA direction, ADX, DXY, US10Y, silver/gold, SP500/Nasdaq, or approved market-specific proxies. Local setup scoring SHALL accept deterministic context-driver signals supplied by upstream data providers, SHALL NOT fetch external context instruments itself, and SHALL record explicit score-penalty or blocking reasons when context drivers oppose the breakout direction.

#### Scenario: Context sharply opposes breakout
- **WHEN** a configured context driver strongly moves against the breakout direction
- **THEN** the system lowers score or rejects the setup according to configuration

#### Scenario: Context driver hard-blocks a setup
- **WHEN** an enabled context driver opposes the breakout side at or above the configured hard-block threshold
- **THEN** setup scoring returns blocked eligibility
- **AND** rejection reasons include `context_filter_blocked` and the driver reason

#### Scenario: Context driver lowers but does not block score
- **WHEN** an enabled context driver opposes the breakout side below the configured hard-block threshold
- **THEN** setup scoring reduces the numeric breakout score by the configured deterministic penalty
- **AND** recalculates normal/reduced/blocked eligibility from the adjusted score

#### Scenario: Context filter is side-aware
- **WHEN** a context driver opposes the opposite breakout side rather than the evaluated side
- **THEN** setup scoring does not penalize or block the evaluated setup because of that driver
