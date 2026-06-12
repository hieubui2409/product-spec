# Decision Register

---
id: DEC-1
status: active
date: 2026-06-12
affects: decision_register.py
---

## DEC-1 — Add decision-register-view sibling for affects-filter and supersede-chain presentation

The decision_register.py file is at 401 LOC (over the 250-LOC module budget). A dedicated view sibling keeps the main register flat: filter_by_affects, render_supersede_chain (cycle-safe, dangling-soft), render_dashboard_row, render_dashboard_summary. The --list --affects PRD-X dispatch adds ~6 LOC to the main file. Reuses parse_decisions() as the single DEC loader (DRY).
