## ADDED Requirements

### Requirement: Breakout reports preserve evidence across universe sizes and cost tiers
Backtesting and portfolio reports SHALL preserve comparable evidence for one-coin, multi-coin, and promoted-universe runs with explicit cost-tier labeling.

#### Scenario: Scorecard is written
- **WHEN** a scorecard is generated for 1, 10, 50, 100, or fixed-universe symbols
- **THEN** the report records universe name, symbol count, symbols or symbol artifact path, windows, thresholds, costs, starting balance when applicable, exposure caps when applicable, status, blockers, and artifact paths.

#### Scenario: Cost assumptions differ
- **WHEN** comparing friction-light and realistic-cost runs
- **THEN** the report labels cost assumptions explicitly
- **AND** does not overwrite positive friction-light concept evidence with realistic-cost robustness failure.

#### Scenario: Documented screener coverage is reported
- **WHEN** implementation evidence is summarized
- **THEN** the report states which source-document algorithm blocks were active and which remained unimplemented or approximated.
