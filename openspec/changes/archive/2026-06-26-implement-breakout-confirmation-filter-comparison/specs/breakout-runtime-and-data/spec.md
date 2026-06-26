# breakout-runtime-and-data Specification Delta

## ADDED Requirements
### Requirement: Breakout confirmation filters preserve no-lookahead semantics
Breakout confirmation filters SHALL use only information available at or before the delayed confirmation entry time.

#### Scenario: Confirmation needs future bars relative to original breakout
- **WHEN** a candidate breakout appears at bar `t`
- **AND** a profile requires confirmation from one or more later bar closes
- **THEN** the backtest MUST NOT enter at bar `t` using those later closes
- **AND** the earliest allowed entry is after the confirmation condition is observable.

#### Scenario: Confirmation fails before entry
- **WHEN** a pending breakout candidate fails the selected confirmation condition before entry
- **THEN** no trade is created for that candidate
- **AND** a deterministic machine-readable skip/cancel reason is counted.

### Requirement: Confirmation filters use OHLCV-only public research data
Breakout confirmation filters SHALL be computed from public OHLCV/context data already present in the research pipeline.

#### Scenario: Microstructure context is considered
- **WHEN** a confirmation idea requires order book, стакан, DOM, L2 depth, footprint, trade tape, taker-flow, private account state, or exchange credentials
- **THEN** that idea is out of scope for this change
- **AND** it must be proposed through a separate OpenSpec change before implementation.

### Requirement: Confirmation profiles preserve default behavior when disabled
Confirmation filter configuration SHALL be disabled by default.

#### Scenario: Reference profile runs
- **WHEN** the reference profile has no confirmation filter configured
- **THEN** existing signal evaluation, entry timing, risk gates, feature filters, and reporting behavior remain unchanged except for empty confirmation reporting fields where applicable.
