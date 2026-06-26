## 1. OpenSpec readiness

- [x] 1.1 Confirm this is a narrow implementation of existing `breakout-backtesting-reporting` OOS gate requirements.
- [x] 1.2 Validate the change and all specs before source implementation.

## 2. Implementation

- [x] 2.1 Add typed local OOS threshold and approval-decision models.
- [x] 2.2 Add a deterministic helper that blocks missing thresholds, unavailable/missing metrics, and failed thresholds.
- [x] 2.3 Keep live execution, production enablement, UI, persistence, deployment, and cloud delivery out of scope.

## 3. Tests and verification

- [x] 3.1 Add targeted unit tests for missing thresholds, passing thresholds, failed thresholds, missing metrics, and unavailable metrics.
- [x] 3.2 Run `uv run pytest`.
- [x] 3.3 Run `uv run ruff check .`.
- [x] 3.4 Run `uv run pyright`.
- [x] 3.5 Run `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`.
- [x] 3.6 Run duplicate spec/archive-name intersection check.
- [x] 3.7 Run self-review against the approved spec and confirm no live execution or unrelated changes were introduced.
