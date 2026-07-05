# Документация SCNR Pro Boy

Этот каталог — единая точка входа для документации проекта. Он разделяет source materials стратегии, операционные runbooks, OpenSpec-контракты и подсказки для кодагентов.

## Быстрый выбор документа

| Задача | Читать сначала | Зачем |
|---|---|---|
| Изменить breakout-логику, scoring, FSM, risk или backtest contracts | `docs/CODEAGENT.md`, затем `docs/ai/task/README.md` | Понять source-of-truth, запреты и связанные specs/code/tests |
| Найти исходную методику стратегии пробоев | `docs/ai/task/README.md` | Разделяет ТЗ, инфографику, PDF и research evidence |
| Работать с локальной эксплуатацией, degraded mode, risk-stop, fake execution | `docs/breakout-operations.md` | Runbook, reason codes и safety checks |
| Создать или проверить OpenSpec change | `openspec/specs/` и relevant `docs/ai/task/source-traceability.md` | Нормативные контракты и traceability |
| Проверить текущий research status по realistic costs | `docs/ai/task/breakout-realistic-cost-timeout-2026-06-28.md` | Negative evidence / pause decision для текущей ветки |

## Состав `docs/`

- `docs/CODEAGENT.md` — порядок чтения и safety rules для AI/code agents.
- `docs/breakout-operations.md` — локальная эксплуатация, degraded-mode checks, security notes, runbook и QA checklist.
- `docs/ai/task/README.md` — индекс source materials для стратегии пробоев.
- `docs/ai/task/source-manifest.yaml` — machine-readable manifest source documents.
- `docs/ai/task/requirements-index.md` — стабильные requirement IDs для ключевых source requirements.
- `docs/ai/task/source-traceability.md` — связь source blocks → OpenSpec specs → likely code areas → tests.
- `docs/ai/task/IMG_2656.transcript.md` — текстовая расшифровка видимых блоков инфографики.
- `docs/ai/task/deep-research-report.md` — основной Russian-first source report / ТЗ.
- `docs/ai/task/breakout-realistic-cost-timeout-2026-06-28.md` — decision record о паузе realistic-cost ветки.
- `docs/ai/task/IMG_2656.JPEG` и `docs/ai/task/Торговля пробоев.pdf` — оригинальные визуальные source materials.

## Что является authoritative

Для стратегии пробоев authoritative source materials:

1. `docs/ai/task/deep-research-report.md`
2. `docs/ai/task/IMG_2656.JPEG`
3. `docs/ai/task/Торговля пробоев.pdf`

Для реализации и safety границ authoritative OpenSpec specs лежат в `openspec/specs/`. Если source document и текущий код расходятся, не исправляй код напрямую: создай или обнови OpenSpec change.

## Что не является разрешением на live trading

Source documents описывают целевую стратегию и режимы вроде advisory-only, semi-auto и full-auto, но текущий репозиторий не получает live/full-auto breakout execution только из-за наличия этих документов.

Перед любым live broker adapter, production deployment, full-auto режимом, credentialed breakout execution или operator dashboard нужен отдельный OpenSpec change.
