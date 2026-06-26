# Design

## Goal
Define a durable governance layer for breakout research work. The layer should answer:

1. What is the current unresolved research hypothesis?
2. What exactly counts as quarterly `8/8` for that hypothesis?
3. Which failing criterion should be attacked next?
4. When should the loop stop with success versus an external blocker?
5. How should archived failed methods and external research be used safely?

## Capability Shape
Create a new capability:

`breakout-research-hypothesis-governance`

This is intentionally separate from `breakout-backtesting-reporting` and `breakout-setup-scoring`. Those capabilities define data, reports, gates, and strategy mechanics. This new capability defines the meta-contract for selecting and driving research hypotheses through those mechanics.

## Hypothesis Discovery
The governance flow should perform bounded local search before reporting no task:

- active OpenSpec changes;
- current specs;
- archived change recommendations;
- diagnostic artifacts referenced by docs or tasks;
- tests and failing/pending criteria;
- local code surfaces with explicit TODO/recommendation markers.

It should not perform broad product discovery. The output must be one current hypothesis or a clear "no bounded hypothesis found" result.

## Quarterly Scorecard
For the BTCUSDT breakout research line, `8/8` means all eight quarterly windows pass configured research thresholds:

- `2023q1`
- `2023q2`
- `2023q3`
- `2023q4`
- `2024q1`
- `2024q2`
- `2024q3`
- `2024q4`

Allowed status values:

- `pass`;
- `fail`;
- `unknown`;
- `blocked`.

Each quarter must identify the command, artifact, metrics, blockers, and evidence needed to verify its status. The current archived reference is `conservative-v1-m15-slope-positive-max-trades-8`, which reached `5/8` and left `2024q1`, `2024q2`, and `2024q4` failing. Future changes should preserve that quarterly framing unless a later reviewed OpenSpec change explicitly changes the evaluation window set.

## Iteration Policy
Each iteration should select one primary failing quarter or shared failure mechanism across failing quarters. Selection should prefer the target that most directly prevents quarterly `8/8`.

After a significant change or research step, the scorecard must be updated. If the score does not improve, the current approach should be stopped or justified with new evidence.

## Archive And External Research
Archived changes are not a source of solutions by default. They are negative evidence:

- what was already tried;
- why it failed;
- which quarters, windows, metrics, or thresholds remained failing;
- which scopes were deferred;
- which blockers were external.

An archived method may be retried only if the new change explicitly identifies which old blocker is no longer present or which new condition makes the method valid.

Research-only subagents may be used when progress stalls. They should inspect local evidence and return facts, dead ends, candidate alternatives, risks, and file paths. They must not mutate the working tree.

arXiv may be used only as a source of ideas for algorithms, experimental design, metrics, failure modes, or validation methods. Paper ideas must be mapped back to local specs, data, tests, and constraints before implementation. Paper-driven complexity is rejected when a simpler local path can reach quarterly `8/8`.

## Stop Conditions
Stop with success only when:

- all eight quarterly windows are `pass`;
- required verification commands or artifacts are recorded;
- OpenSpec validation passes;
- no scope guard is violated;
- a concise Telegram success notification is sent or the send failure is recorded.

The Telegram success notification should include the change id, profile/hypothesis, passed quarter list, key thresholds or metrics, artifact or summary paths, local commit hash when available, and confirmation that push/MR/merge/live trading/private API were not performed.

Stop with a blocker only when:

- a required quarter cannot be evaluated or fixed locally;
- the missing input, data, access, command, or owner decision is explicit;
- previous local attempts and research evidence are summarized.

## Risks
- A governance capability can become too abstract. Keep scenarios concrete and tied to quarterly research artifacts, scorecards, and OpenSpec changes.
- The runner could create too many changes. Require exactly one narrow change per selected hypothesis.
- arXiv could encourage excessive complexity. Require local fit and simplest-successful-path selection.
