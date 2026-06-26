# Design

## Scope

Implement one deterministic local gate that consumes an existing `BacktestReport` and an explicit threshold configuration. The gate only returns approval/blocking metadata; it must not place orders, mutate broker state, or imply production readiness outside the configured checks.

## Contract

1. Add a typed threshold DTO for production OOS/business-validity review.
   - Numeric thresholds are optional, but at least one threshold must be configured before approval can pass.
   - Supported v1 metrics are those already present in `BacktestReport.metrics`: `oos_performance`, `max_drawdown`, `win_rate`, `profit_factor`, and `trade_count`.
2. Add a typed gate decision DTO with:
   - `approved: bool`;
   - machine-readable `reason`;
   - checked metric payloads;
   - explicit blockers for missing thresholds, unavailable metrics, missing metrics, and failed thresholds.
3. Add a pure helper in the backtesting/reporting module so tests and later release review code can call the same local gate.
4. Keep defaults fail-closed: no thresholds means blocked.

## Risks / Mitigations

- Risk: Treating this as production trading approval. Mitigation: name it as a local report gate only and keep production full-auto/live execution still blocked by deferred-scope specs.
- Risk: Metric sign ambiguity for drawdown. Mitigation: compare `max_drawdown` as a lower-bound value where more negative is worse, matching current report semantics.
- Risk: Silent pass when a metric is unavailable. Mitigation: block if a configured metric has an unavailable reason, is missing, or is `None`.

## Verification

- OpenSpec strict validation for the change and all specs.
- Targeted pytest coverage for missing thresholds, passing thresholds, failed thresholds, missing metrics, and unavailable metrics.
- Project quality gates: `uv run pytest`, `uv run ruff check .`, `uv run pyright`, and `git diff --check`.
