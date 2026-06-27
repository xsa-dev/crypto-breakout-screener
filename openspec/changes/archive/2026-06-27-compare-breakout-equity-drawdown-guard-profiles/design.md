# Design

## Hypothesis
The selected mechanism is a realized equity drawdown guard layered on large-target exit profiles. Recent large-target realistic-cost evidence shows `2024q1` can have strong positive net/PF while still failing `max_drawdown_below_threshold`; a causal guard that stops new entries after realized peak-to-trough drawdown reaches 30% may cap the failing drawdown path while preserving the larger average-trade profile needed for realistic costs.

## Fixed candidate set
- `conservative-v1-m15-slope-positive-max-trades-8-target-3p0-hold-32-drawdown-30pct`: intrabar `3.0 ATR` target, max-hold 32 M15 bars, stop new entries when realized equity drawdown reaches 30% from the run peak.
- `conservative-v1-m15-slope-positive-max-trades-8-target-4p0-hold-32-drawdown-30pct`: intrabar `4.0 ATR` target, max-hold 32 M15 bars, same 30% realized drawdown guard.
- `conservative-v1-m15-slope-positive-max-trades-8-close-target-2p0-hold-32-drawdown-30pct`: close-confirmed `2.0 ATR` target, max-hold 32 M15 bars, same 30% realized drawdown guard.

These candidates are fixed, named, and not an optimizer. If none reaches realistic-cost `8/8`, the hypothesis is falsified for this slice.

## Implementation details
- Add a disabled-by-default `max_realized_drawdown` field to `BacktestResearchGateConfig`.
- Track realized equity and peak equity in `ResearchGateState` after closed trades only.
- `_research_gate_reason` skips a new entry with `skipped_max_realized_drawdown` when `(peak_equity - current_equity) / initial_equity >= max_realized_drawdown` before the entry decision.
- Existing `risk_control_settings_json` and `risk_control_skip_counts_json` should expose the guard because it is a realized-state risk control, while `exit_profile_settings_json` continues to expose target/hold behavior.
- Reuse existing target-only exit implementation for target/holding semantics; add profile resolution tests and a focused gate-state test.

## Constraints
- Keep entry scoring, sizing, M15 slope feature filter, max-trades setting, confirmation/regime filters, scorecard windows, cost settings, and thresholds unchanged.
- Use only realized completed-trade equity state; do not inspect open-trade path, current trade outcome, or future bars when deciding to skip.
- No private/live API, account data, order placement, production approval, push, MR, merge, or Telegram success unless realistic-cost `8/8` is achieved after archive/commit.

## Verification strategy
1. Add/adjust tests for drawdown guard default-disabled behavior, causal skip after realized drawdown breach, named profile resolution, and summary serialization.
2. Run strict OpenSpec validation before source implementation.
3. Run targeted tests and full project gates.
4. Run cached public-data realistic-cost batches for candidates. Early falsify a candidate only after a required realistic-cost quarter fails; record remaining windows as blocked/not run.
5. Archive as successful only on realistic-cost `8/8`; otherwise archive as falsified research evidence with scorecard artifacts.
