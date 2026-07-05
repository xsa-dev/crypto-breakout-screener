# Source materials for breakout strategy

Эта директория содержит исходные материалы и research evidence для breakout-стратегии SCNR Pro Boy. Не все файлы имеют одинаковую роль: source strategy documents задают целевую методику, а research records описывают результаты текущих гипотез.

## Inventory

| File | Role | Status | Use for | Do not use for |
|---|---|---|---|---|
| `deep-research-report.md` | `authoritative_strategy_source` | authoritative | Strategy rules, FSM, architecture, config/storage, testing, acceptance, security | Claiming current profitability or live readiness |
| `IMG_2656.JPEG` | `visual_source` / `authoritative_strategy_source` | authoritative visual source | Visual confirmation of strategy blocks, percentages, score/risk blocks | Grep/RAG without transcript |
| `IMG_2656.transcript.md` | `text_companion` | indexing companion | Text search and agent retrieval for the infographic | Replacing the original image when exact visual layout matters |
| `Торговля пробоев.pdf` | `visual_source` / `authoritative_strategy_source` | authoritative original PDF | Source-method confirmation after extraction/OCR | Retrieval without extracted text |
| `breakout-realistic-cost-timeout-2026-06-28.md` | `research_evidence` | current negative evidence / pause decision | Research planning, robustness claims, what not to promote | Rewriting source strategy semantics |
| `source-manifest.yaml` | `manifest` | maintained index | Machine-readable source metadata | Strategy semantics by itself |
| `requirements-index.md` | `traceability_index` | maintained index | Stable requirement IDs | Replacing OpenSpec normative specs |
| `source-traceability.md` | `traceability_index` | maintained index | Mapping source blocks to specs/code/tests | Replacing tests or implementation review |

## Recommended use

Before changing breakout behavior:

1. Find relevant source block here.
2. Find requirement IDs in `requirements-index.md`.
3. Check `source-traceability.md` for OpenSpec capability, likely code area, and tests.
4. Read the relevant canonical spec under `openspec/specs/`.
5. Create or update an OpenSpec change before code edits.

## Important distinctions

- Source strategy documents describe the intended method; they do not approve live/full-auto trading in this repository.
- The timeout decision record is negative evidence for a current realistic-cost research branch; it does not invalidate every unimplemented source block.
- The PDF currently needs reliable extraction/OCR before it becomes fully text-indexable.
- The JPEG transcript is a reading aid; when precision matters, inspect the original image too.
