# Proposal

## Why

The repository currently has two documentation roots:

- `docs/` contains operator-facing documentation such as `docs/breakout-operations.md`.
- the legacy `doc` tree contains source research materials for the breakout strategy, including `deep-research-report.md`, `breakout-realistic-cost-timeout-2026-06-28.md`, `Торговля пробоев.pdf`, and `IMG_2656.JPEG`.

This split is confusing for navigation and caused the user to ask to объединить `doc` and `docs`. A single documentation tree should make the repository easier to browse without changing the meaning of the source materials.

## What Changes

Consolidate the documentation directory layout by moving the current source materials under `docs/ai/task/` and removing the obsolete `doc/` tree after migration.

Proposed canonical layout:

- keep `docs/breakout-operations.md` where it is;
- move source research files to `docs/ai/task/*`;
- update all repository references to use `docs/ai/task/...`;
- update OpenSpec canonical specs and archived traceability/proposal references only as needed for path accuracy;
- remove stray `.DS_Store` files under `doc/` rather than migrating them.

## Success Criteria

- There is no tracked or useful untracked `doc/` content left after migration.
- Source research materials are available under `docs/ai/task/`.
- References in README/OpenSpec/docs point to the new `docs/ai/task/` paths.
- OpenSpec validation and `git diff --check` pass.
- No source code, dependencies, lockfile, runtime behavior, generated research outputs, or trading logic are changed.

## Non-goals

- No rewrite of the research documents' content.
- No changes to breakout strategy semantics or capability specs beyond path references.
- No generated artifact migration.
- No commit, archive, or push unless separately requested.
