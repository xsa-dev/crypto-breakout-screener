# Proposal

## Why
The autonomous breakout research loop can currently stop too early when no active OpenSpec change exists, even though the repository contains archived diagnostics, deferred research gates, and candidate follow-up hypotheses. This makes the runner report "local tasks absent" instead of reconstructing the next research goal and driving it toward a measurable outcome.

The project needs a durable OpenSpec capability that defines how research hypotheses are selected, scored, pursued, and stopped. The contract must keep the goal fixed, require a concrete quarterly `8/8` scorecard for the BTCUSDT 2023q1-2024q4 research line, prevent repeating archived dead ends, and allow bounded external research such as arXiv only when local evidence is insufficient.

## What Changes
- Add a new `breakout-research-hypothesis-governance` capability.
- Define how to discover the current unresolved hypothesis from specs, archived recommendations, docs, tests, and local code.
- Require every BTCUSDT breakout research hypothesis to produce an explicit eight-quarter scorecard before implementation.
- Require each iteration to target the highest-impact failing, unknown, or blocked criterion.
- Define archive usage as negative evidence and constraint discovery rather than a source of ready-made solutions.
- Allow research-only subagents and arXiv as bounded sources of alternative ideas when progress stalls.
- Define success and stop conditions: all eight quarterly windows pass configured research thresholds with a Telegram success notification, or a clear external blocker.

## Out of Scope
- Implementing any specific trading filter, risk-control profile, ML model, optimizer, live adapter, UI, or production approval.
- Changing current strategy thresholds, research thresholds, or production deferred-scope gates.
- Running new BTCUSDT experiments under this change.
- Archiving past changes or rewriting existing research evidence.

## Expected Outcome
Future autonomous cycles have a repository-level contract that forces hypothesis discovery and measurable quarterly `8/8` pursuit before declaring there are no local tasks. The contract should make the runner more useful without authorizing broad, unbounded discovery or weakening existing OpenSpec discipline.
