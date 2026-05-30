<!--
TEMPLATE: impact-report.md — the per-change impact report written to
docs/product/impact/<ts>.md by the impact-pass (runs on --update AND --validate).

The impact-pass is the per-CHANGE propagation surface (downstream() + LLM
interpretation), distinct from the per-ARTIFACT validation-catalog checks
(risk_blindspot / time_realism / competitive_drift). Keep them separate.

Structure (report §5.2):
  changed set → spec_graph.downstream() [deterministic] → for each affected node
  the LLM tags {dim_touched, one_liner, action}. An affected node that is
  `approved` AND contradicted runs the contradiction protocol (keep/change/hybrid)
  — the engine NEVER auto-flips an approved artifact (G-A3).

The affected-node table rows are produced by the LLM annotation pass; this
template fixes only the heading + column order so every impact report is
shaped the same. Bilingual headings localize per `lang`; IDs/dims/enums stay
English (CLAUDE.md → Bilingual Conventions).
-->

# Impact Report — {{date}} | Báo cáo tác động — {{date}}

- **Trigger | Kích hoạt:** {{trigger}}            <!-- --update | --validate -->
- **Changed | Thay đổi:** {{changed_set}}         <!-- the change-set: 1 id (--update) or the snapshot-delta ids (--validate) -->
- **Dimensions touched | Chiều bị ảnh hưởng:** {{dims}}   <!-- union of dim_touched across affected nodes, e.g. [risk, time] -->

## Affected downstream | Ảnh hưởng phía dưới

<!--
One row per affected node returned by downstream(). dim_touched ∈
{scope, risk, time, competition, ac, traceability}; one_liner = a single LLM
sentence on HOW the change touches this node; action = a concrete suggestion
(review / split / re-estimate / re-approve / no-op).
-->

| Node | Dim touched | Interpretation (1-liner) | Suggested action |
|------|-------------|--------------------------|------------------|
{{rows}}

<!-- OPTIONAL: contradictions -->
## Contradictions with approved artifacts | Mâu thuẫn với tài liệu đã duyệt

<!--
Listed ONLY when an affected node is `status: approved` AND the change
contradicts its content. Each is surfaced to the PO via the contradiction
protocol (keep / change / hybrid); the engine never auto-flips. See
references/validation-rules-spec.md → Contradiction Protocol.
-->

{{contradictions}}
<!-- /OPTIONAL -->
