## ADDED Requirements

### Requirement: Algorithmic breakout score ranks entry-time setup quality
The breakout setup scoring system SHALL provide an opt-in deterministic 0..100 algorithmic score using only entry-time public features.

#### Scenario: Score is computed
- **WHEN** `algorithmic-breakout-score-v1` evaluates a candidate
- **THEN** it records total score, component scores, eligibility bucket, and rejection reasons
- **AND** component scores include cost feasibility, BTC/ETH regime, market breadth, relative strength, volatility compression, volume/activity expansion, ATR breakout distance, and multi-timeframe trend alignment.

#### Scenario: Score blocks weak candidates
- **WHEN** total score is below 70
- **THEN** score-aware portfolio selection blocks the candidate with `portfolio_selection_algorithmic_score_below_threshold`
- **AND** the skipped candidate remains in audit artifacts.

#### Scenario: Score avoids outcome leakage
- **WHEN** score inputs are collected
- **THEN** the implementation uses only data available at or before candidate time
- **AND** does not use realized PnL, exit price, future bars, or archived contribution rankings.
