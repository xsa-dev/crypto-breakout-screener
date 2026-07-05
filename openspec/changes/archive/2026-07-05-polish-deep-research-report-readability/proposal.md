# Proposal

## Why

`doc/ai/task/deep-research-report.md` is an important Russian source document for the breakout strategy, but it currently has readability and rendering problems:

- raw citation placeholders such as `cite...` and `filecite...` leak into the document and render as broken glyphs in normal Markdown viewers;
- the current H1 title is an outdated generic name and does not match the repository identity;
- several very long paragraphs are hard to scan in terminal, GitHub, and editor preview;
- Mermaid `xychart-beta` examples are not reliably rendered by all Markdown viewers;
- dense sections would benefit from clearer Russian section naming, short summaries, and preserved tables/code blocks.

The user explicitly asked to make the file readable and fix rendering errors. This should be a documentation-only polish pass that preserves the technical content and does not change code, specs semantics, dependencies, or generated research artifacts.

## What Changes

Rewrite and polish `doc/ai/task/deep-research-report.md` for readable Russian Markdown:

- remove or replace broken raw citation placeholders with readable source notes or a short note that the original source references were embedded in the generated report;
- update the document title to match the repository name while preserving the subtitle/meaning that it is a breakout strategy technical brief;
- split long paragraphs into shorter paragraphs or bullets while preserving meaning;
- keep the main prose Russian-first;
- preserve key tables, parameters, algorithms, JSON config example, state machine, architecture diagram, acceptance criteria, security notes, and research requirements;
- replace Mermaid snippets that commonly fail to render with more reliable Markdown tables or Mermaid diagrams, or mark them as optional if retained;
- avoid new unsupported capability claims, live-trading claims, or implementation behavior changes.

## Success Criteria

- `doc/ai/task/deep-research-report.md` renders cleanly in normal Markdown preview without visible `...` citation artifacts.
- The H1 title uses the repository name rather than the outdated generic title.
- The main document remains Russian-first and easier to scan.
- Technical content is preserved: strategy stages, entry modes, risk rules, FSM, architecture modules, config parameters, testing/acceptance, docs/security sections.
- The change touches only the target documentation file and OpenSpec process artifacts.
- No secrets, credentials, `.env` values, private endpoints, dependency changes, source changes, generated artifacts, or research result claims are introduced.

## Non-goals

- No Python/source-code changes.
- No dependency or lockfile changes.
- No changes to trading logic, backtest behavior, OpenSpec capability semantics, or generated artifacts.
- No attempt to re-source or verify external citations online.
- No commit, archive, or push unless separately requested.
