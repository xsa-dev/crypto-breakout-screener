# Design

## Scope

This is a documentation-layout change only. The canonical documentation root becomes `docs/`.

## Current inventory

`docs/` currently contains:

- `docs/breakout-operations.md`

The legacy source-material directory currently contains:

- `deep-research-report.md`
- `breakout-realistic-cost-timeout-2026-06-28.md`
- `IMG_2656.JPEG`
- `Торговля пробоев.pdf`

Stray macOS metadata files were observed under `doc/` and should not be migrated:

- `doc/.DS_Store`
- `doc/ai/.DS_Store`

## Migration plan

1. Create `docs/ai/task/`.
2. Move the useful source-material files into `docs/ai/task/` using git-aware moves where possible.
3. Remove `.DS_Store` files and the now-empty `doc/` directories.
4. Update path references in:
   - `README.md` if needed;
   - canonical OpenSpec specs under `openspec/specs/`;
   - active OpenSpec changes under `openspec/changes/`;
   - archived OpenSpec traceability/proposal/design/task files only where they point to the source materials.
5. Do not alter the content of source research documents except for path references if a document contains self-references.

## Path mapping

| Source material | New path |
|---|---|
| `deep-research-report.md` | `docs/ai/task/deep-research-report.md` |
| `breakout-realistic-cost-timeout-2026-06-28.md` | `docs/ai/task/breakout-realistic-cost-timeout-2026-06-28.md` |
| `IMG_2656.JPEG` | `docs/ai/task/IMG_2656.JPEG` |
| `Торговля пробоев.pdf` | `docs/ai/task/Торговля пробоев.pdf` |

## Verification

After implementation:

- `npx --yes @fission-ai/openspec@1.4.1 validate consolidate-doc-and-docs-directories --strict --no-interactive`
- `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`
- `git diff --check`
- targeted path sanity script:
  - confirm all expected files exist under `docs/ai/task/`;
  - confirm no useful content remains under `doc/`;
  - confirm no text references remain to the legacy source-material path.

Full Python lint/type/test gates are not required because no code changes are in scope.
