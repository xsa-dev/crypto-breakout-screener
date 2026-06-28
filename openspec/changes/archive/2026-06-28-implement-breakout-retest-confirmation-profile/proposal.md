# Proposal

## Why

The source breakout concept treats confirmation and retest as first-class parts of the setup. The simplified portfolio profile can enter too early, before the breakout proves continuation. A separate retest/confirmation profile is needed to test whether waiting for confirmation or a held retest improves robustness without changing costs or thresholds.

## What Changes

Add opt-in retest/confirmation behavior for breakout candidates.

The profile SHALL:

- require configured close/tick confirmation beyond the breakout level and buffer;
- optionally require retest of the breakout zone within configured bars;
- require retest hold/continuation evidence before accepting the trade when retest mode is enabled;
- preserve blocked/delayed candidates with explicit blockers.

## Success Criteria

- Missing confirmation blocks with `portfolio_selection_confirmation_missing`.
- Missing retest blocks with `portfolio_selection_retest_missing` when retest is required.
- Failed retest blocks or exits with `portfolio_selection_retest_failed`.
- Retest/confirmation decisions are reported by quarter, regime, and lifecycle state.

## Non-goals

- No new score formula, no top-N allocation, no fast-failure exit, no cost change, no threshold weakening.
