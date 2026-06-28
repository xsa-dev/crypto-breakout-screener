# Proposal

## Why

The owner goal is not to invent a new trading strategy. The primary product goal is to implement a breakout screener/trading-system research loop based on the supplied source documentation in `doc/ai/task`:

- `deep-research-report.md`;
- `Торговля пробоев.pdf`;
- `IMG_2656.JPEG`.

The documentation defines the intended algorithm: level search, setup preparation, breakout score, three entry modes, confirmation, retest, additions, false-breakout handling, 30/50/20 exits, risk management, logging, and historical reports.

Historical evidence already matters:

- earlier low/friction-light cost runs reaching `8/8` are positive evidence that the documented breakout idea has signal under favorable execution assumptions;
- realistic-cost shared-bankroll failures are robustness and execution-cost evidence, not proof that the documented screener concept is invalid;
- tests over one coin, ten coins, fifty coins, and later broader universes are all part of the evidence log, provided each run states universe, costs, thresholds, and artifacts.

This change anchors all active implementation changes to the documented screener objective so autonomous work does not drift into unrelated strategy invention or overfit only to a net-of-cost portfolio score.

## What Changes

Add a governance contract for the documented breakout screener:

- source docs are the primary algorithmic specification;
- OpenSpec changes must map their implementation to the source-doc algorithm block they cover;
- historical evidence must be preserved across universes and cost assumptions;
- `8/8` under friction-light costs is recorded as positive concept evidence;
- realistic-cost `8/8` remains a stronger robustness target, not a replacement for implementing the documented screener.

## Success Criteria

- Research reports distinguish `concept_evidence`, `friction_light_evidence`, `realistic_cost_evidence`, and `falsified_or_blocked_evidence`.
- Each algorithmic implementation change names the source documentation block it implements.
- Scorecards over 1, 10, 50, 100, or fixed universes are allowed as evidence when they report universe, costs, thresholds, windows, and artifact paths.
- Autonomous prompt directs the agent to implement the documented screener/trading-system algorithm first, then evaluate robustness.

## Non-goals

- No new strategy family outside the supplied breakout documentation.
- No claim that friction-light `8/8` is production-ready realistic-cost proof.
- No weakening of reporting, audit, or cost disclosure.
