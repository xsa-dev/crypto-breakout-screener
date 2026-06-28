# Design

## Lifecycle model

Represent lifecycle as deterministic candidate metadata. The first implementation may use booleans or nullable timestamps, but the artifact schema must preserve the order:

`level_found -> compression -> approach -> breakout -> confirmation -> retest -> continuation -> failure_exit`.

## Candidate preservation

Rejected candidates must not disappear. They must retain:

- symbol/window;
- entry or candidate timestamp;
- furthest lifecycle state;
- blocker;
- source artifact path.

## Reporting

Portfolio artifacts SHALL include:

- lifecycle columns in trade/candidate CSVs;
- `lifecycle_state_counts` in summary JSON;
- per-regime lifecycle counts when portfolio regime labels are available.

## Compatibility

Existing profiles may ignore lifecycle fields. This change creates auditability and inputs for later algorithmic score, retest/confirmation, and fast-failure changes.
