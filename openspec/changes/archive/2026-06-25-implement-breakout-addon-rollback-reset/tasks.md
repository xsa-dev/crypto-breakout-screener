## 1. OpenSpec readiness
- [x] 1.1 Confirm the change is a narrow implementation delta under `breakout-risk-position-execution`.
- [x] 1.2 Validate proposal/spec/tasks before source edits.

## 2. Implementation
- [x] 2.1 Add a local add-on rollback decision DTO.
- [x] 2.2 Add side-symmetric rollback evaluation to `RiskManager` with no broker side effects.
- [x] 2.3 Add focused tests for rollback reduction, hold behavior, and invalid quantity.

## 3. Verification and landing
- [x] 3.1 Run OpenSpec validation for the change and all specs.
- [x] 3.2 Run targeted/full pytest, Ruff, Pyright, and git diff checks.
- [x] 3.3 Self-review the diff against the approved spec and confirm no live execution or unrelated changes were introduced.
- [x] 3.4 Mark tasks complete, archive the change, verify no duplicate specs, and create one local commit.
