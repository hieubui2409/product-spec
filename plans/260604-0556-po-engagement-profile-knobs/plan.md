---
title: "PO Engagement Profile knobs for product-spec*"
description: ""
status: pending
priority: P2
branch: "claude/agent-naming-conventions-cd70n"
tags: []
blockedBy: []
blocks: []
created: "2026-06-04T06:01:44.396Z"
createdBy: "ck:plan"
source: skill
---

# PO Engagement Profile knobs for product-spec*

## Overview

Add a **learned-but-confirmed PO engagement profile** to `product-spec*`: 3 new knobs in the existing
`preferences.yaml` that modulate AI engagement (challenge depth, action-suggestion density, standing reminders),
captured via flag + hybrid `--reflect` harvest (always PO-confirmed). **No breaking changes** — all additive keys;
`load()` default-fills, `save()` drops-unknown. Design source:
`plans/reports/brainstorm-design-260604-0556-po-engagement-profile-knobs-report.md`.

New keys: `interview_rigor` (light/standard/**deep**), `action_prompting` (minimal/standard/**proactive**),
`standing_reminders` (`list[str]`, default `[]`). `detail_level` (existing) is referenced, never copied.

Injection: product-spec interview/prose gets all 3; product-spec-critique gets only `action_prompting` +
`standing_reminders` (rigor stays owned by `critique_level`). Mode: `--tdd` (Python logic test-first), red-team gate
after.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Schema and write-CLI in preferences](./phase-01-schema-and-write-cli-in-preferences.md) | Pending |
| 2 | [Product-spec interview/prose injection](./phase-02-product-spec-interview-prose-injection.md) | Pending |
| 3 | [Critique injection (action+reminders only)](./phase-03-critique-injection-action-reminders-only.md) | Pending |
| 4 | [Capture: flag + hybrid reflect harvest](./phase-04-capture-flag-hybrid-reflect-harvest.md) | Pending |
| 5 | [Docs sync](./phase-05-docs-sync.md) | Pending |

## Dependencies

Builds on (all `done`): `260601-1853-product-spec-guardrails-and-memory-layer` (preferences/3D/3E),
`260602-0026-strengthen-memory-write-enforcement` (memory_gap/reflect), `260602-1528-spec-critique-...split-detail-level`
(detail_level vs critique_detail_level split). No unfinished overlapping plans → no `blockedBy`/`blocks` set.

## Non-Breaking Invariant (applies to every phase)

- Additive only: new keys in `preferences.py` `DEFAULTS` + `ENUMS`; never rename/remove existing keys.
- Old `preferences.yaml` (no new keys) must resolve to documented defaults — assert in `test_preferences.py`.
- Knobs are **referenced** at read points, never copied into another store (DRY).
- Every learned value is **PO-confirmed before write** (flag = explicit; harvest = propose→confirm).
