## 1. OpenSpec readiness
- [x] 1.1 Confirm this change only defines research-hypothesis governance and does not implement a trading strategy change.
- [x] 1.2 Confirm existing domain specs do not already define hypothesis discovery and quarterly `8/8` scorecard governance.
- [x] 1.3 Confirm this does not authorize live trading, private API access, production approval, UI work, ML implementation, or optimization search.
- [x] 1.4 Validate this OpenSpec change in strict mode.

## 2. Specification
- [x] 2.1 Add `breakout-research-hypothesis-governance` delta spec.
- [x] 2.2 Define bounded hypothesis discovery before reporting "local tasks absent".
- [x] 2.3 Define the required eight-quarter scorecard and statuses.
- [x] 2.4 Define archive evidence rules so old failed methods are not copied as solutions.
- [x] 2.5 Define research-only subagent and arXiv usage constraints.
- [x] 2.6 Define success and blocker stop conditions.
- [x] 2.7 Define Telegram success notification for completed quarterly `8/8`.

## 3. Verification
- [x] 3.1 Run strict validation for this change.
- [x] 3.2 Run strict validation for all OpenSpec specs.
- [x] 3.3 Run `git diff --check`.

## 4. Archive readiness
- [x] 4.1 After validation, archive the change through the normal OpenSpec workflow when the owner approves. Evidence: archived as `openspec/changes/archive/2026-06-26-define-breakout-research-hypothesis-governance/`.
- [x] 4.2 Confirm the final main spec has no duplicate spec/archive names after archive. Evidence: duplicate-name intersection check returned `[]` after archive.
