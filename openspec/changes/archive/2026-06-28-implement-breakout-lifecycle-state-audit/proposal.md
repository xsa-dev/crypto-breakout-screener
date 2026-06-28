# Proposal

## Why

The tested portfolio behavior is too close to a mechanical breakout screener. The source concept requires a lifecycle: level discovery, compression, approach, breakout, confirmation, retest, continuation, and failure. Without explicit lifecycle evidence, later score/ranking rules cannot distinguish a mature setup from a raw breakout candle.

## What Changes

Add deterministic lifecycle state audit for every breakout candidate in symbol and portfolio artifacts.

Required states:

- `level_found`;
- `compression`;
- `approach`;
- `breakout`;
- `confirmation`;
- `retest`;
- `continuation`;
- `failure_exit`.

The runner SHALL preserve skipped candidates with their furthest reached state and blocker.

## Success Criteria

- Trade/candidate artifacts expose lifecycle state booleans or timestamps.
- Portfolio trade rows retain lifecycle evidence for accepted and skipped candidates.
- Lifecycle state counts are reported per quarter and per regime.
- Default behavior remains unchanged unless lifecycle-aware profiles use the new fields.

## Non-goals

- No new score, no top-N allocation, no retest entry rule, no fast-failure exit behavior, no threshold weakening, no private/live API.
