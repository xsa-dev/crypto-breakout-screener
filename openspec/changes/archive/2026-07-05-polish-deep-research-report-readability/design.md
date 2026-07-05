# Design

## Scope

Documentation-only readability pass for:

- `docs/ai/task/deep-research-report.md`

Allowed edits:

- prose restructuring;
- section title cleanup;
- updating the H1 title to match the repository name;
- paragraph splitting;
- replacing raw citation artifacts with readable non-broken notes;
- fixing Markdown rendering problems;
- preserving or simplifying diagrams/tables when that improves preview reliability.

Forbidden edits:

- Python/source code changes;
- dependency/lockfile changes;
- generated artifact changes;
- semantic changes to OpenSpec capability specs beyond this change delta;
- new claims that live/full-auto breakout execution is implemented.

## Observed rendering/readability issues

A pre-change scan found:

- 19 occurrences of raw `...` citation artifacts;
- outdated top-level title (`# Техническое задание на разработку торговой системы стратегии пробоев`) that should be replaced with the repository name;
- 2 `xychart-beta` Mermaid snippets, which are beta syntax and not reliably rendered by every Markdown preview;
- 32 lines longer than 180 characters, including several 400+ character prose lines;
- dense source-report prose that needs shorter Russian paragraphs for terminal and GitHub readability.

## Implementation approach

1. Keep the document as a ТЗ/source report, not a README.
2. Change the H1 title to the repository name (`SCNR Pro Boy`) and keep the breakout trading-system ТЗ meaning as a subtitle or first descriptive heading.
3. Add a short note near the top explaining that broken generated citation markers were removed during readability cleanup while preserving the substantive requirements.
4. Remove all raw citation glyph artifacts from prose.
5. Split dense paragraphs into shorter Russian paragraphs and bullets.
6. Preserve all substantive sections:
   - executive summary / overview;
   - project contour and automation subject;
   - strategy rules and trading logic;
   - algorithmic model and finite-state machine;
   - architecture, modules, integrations;
   - parameters/config/storage;
   - testing/acceptance/reporting;
   - documentation/security/legal recommendations.
7. Keep fenced code blocks valid Markdown. Prefer stable `mermaid` flow/state diagrams; replace `xychart-beta` chart examples with Markdown tables if needed.
8. Do a final scan for raw citation artifacts, path scope, H1 title, and Markdown fence balance.

## Verification

After implementation:

- `npx --yes @fission-ai/openspec@1.4.1 validate polish-deep-research-report-readability --strict --no-interactive`
- `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`
- `git diff --check`
- targeted Markdown sanity script:
  - confirm `docs/ai/task/deep-research-report.md` has no `` artifacts;
  - confirm fenced code blocks are balanced;
  - report remaining lines over 220 characters;
  - confirm the H1 title matches the repository name;
  - confirm key headings still exist.

Full Python test/lint/type gates are not required for this documentation-only source-report cleanup, but may be run if there is uncertainty about accidental source changes.
