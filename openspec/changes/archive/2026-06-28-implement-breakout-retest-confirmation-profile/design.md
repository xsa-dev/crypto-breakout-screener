# Design

## Confirmation rule

Use configured breakout level, side, buffer, and close/tick requirements. If confirmation is unavailable or fails, mark the candidate with `portfolio_selection_confirmation_missing` for profile-aware selection.

## Retest rule

When retest mode is enabled:

- search only bars after breakout and within the configured retest window;
- require price to revisit the breakout zone within tolerance;
- require structure to hold and continuation evidence to appear;
- block missing retest as `portfolio_selection_retest_missing`;
- block failed retest as `portfolio_selection_retest_failed`.

## Reporting

Artifacts SHALL include:

- confirmation pass/fail counts;
- retest missing/failed/pass counts;
- decision reason in candidate/trade ledger;
- per-regime and per-quarter ratios.

## Data rules

The retest decision may inspect bars after the initial breakout only up to the configured retest decision point. It must not inspect final PnL or bars beyond the decision horizon.
