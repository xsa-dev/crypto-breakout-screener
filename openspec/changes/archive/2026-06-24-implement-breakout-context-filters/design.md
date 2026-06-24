## Design

### Scope

This change implements the existing `breakout-setup-scoring` context-filter requirement using local, already-supplied context driver signals. The scorer remains deterministic and does not fetch external instruments itself.

### Data contract

A context driver signal records:

- `name` — stable driver label such as `DXY`, `US10Y`, `SILVER_GOLD`, or a project-specific proxy.
- `opposes_side` — the breakout side the driver opposes.
- `strength` — normalized opposition strength from `0.0` to `1.0`.
- `reason` — optional machine-readable reason to include in traces.

Context filter config records whether filters are enabled, the hard-block threshold, and score penalty per full-strength opposing driver.

### Scoring behavior

`SetupEvaluator.score(...)` accepts optional context drivers. It calculates the base feature score first, then applies context filters:

- disabled filters or empty drivers leave the score unchanged;
- opposing drivers below the hard-block threshold reduce total score by a deterministic penalty proportional to the strongest opposing signal;
- opposing drivers at or above the hard-block threshold set eligibility to `blocked` and add explicit context rejection reasons;
- drivers opposing the opposite side do not penalize the current side.

### Safety boundaries

This change has no network calls, no credentials, no live broker actions, no persistence migration, and no full-auto production enablement.
