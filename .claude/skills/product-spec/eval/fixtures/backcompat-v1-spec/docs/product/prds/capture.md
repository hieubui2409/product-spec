---
id: PRD-CAPTURE
type: prd
brd_goals: [BRD-G1]
status: approved
lang: en
owner: Jane Doe
version: 1.0.0
created: 2026-05-28
updated: 2026-05-28
personas: [writer]
scope: core-value
moscow: must
horizon: now
metrics: [capture-latency]
---

# Capture PRD

## Overview & Problem

Capturing a note must be effortless and instant.

## Personas

- writer

## Use Cases / Flows

1. Writer opens the app.
2. Writer types a note.
3. Note is saved automatically.

## Functional Requirements (MoSCoW)

### Must

- One-tap new note.
- Auto-save on every keystroke.

### Should

- Offline capture.

## Non-Functional Requirements

- New-note ready in under 200ms.

## Success Metrics → BRD Goals

- capture-latency -> BRD-G1 (low friction drives weekly active use).
