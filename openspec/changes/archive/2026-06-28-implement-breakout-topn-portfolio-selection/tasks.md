## 1. Implementation
- [x] 1.1 Add top-N/concurrency bucket settings to portfolio selection.
- [x] 1.2 Sort candidates by score, relative strength, friction, and symbol tie-breaker.
- [x] 1.3 Apply shared-bankroll allocation after ranking.
- [x] 1.4 Preserve rank-skipped candidates with `portfolio_selection_rank_not_selected`.
- [x] 1.5 Export ranking values and selection counts.

## 2. Tests
- [x] 2.1 Test higher-score concurrent candidate is selected before lower-score candidate.
- [x] 2.2 Test deterministic tie-breaker produces stable output.
- [x] 2.3 Test rank-skipped candidates do not consume exposure or PnL.
- [x] 2.4 Test default behavior remains unchanged.

## 3. Verification
- [x] 3.1 Run targeted portfolio selection tests.
- [x] 3.2 Run strict OpenSpec validation.
- [x] 3.3 Run `git diff --check`.
