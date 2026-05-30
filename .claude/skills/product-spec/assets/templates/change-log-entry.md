<!--
TEMPLATE: change-log-entry.md — fragment appended to docs/product/change-log.md
on every --update / --approve / generate flow.
Format: one entry per change, append-only, newest at top.
-->

## {{date}} — {{change_type}} | {{change_type_vi}}

- **Artifact | Tài liệu:** {{artifact_id}} ({{file}})
- **Action | Hành động:** {{action}}
- **Reason | Lý do:** {{reason}}
- **Affected downstream | Ảnh hưởng phía dưới:** {{affected_set}}
- **Dimensions touched | Chiều bị ảnh hưởng:** {{dims}}
- **Author | Tác giả:** {{author}}

<!-- OPTIONAL: detail -->
**Detail | Chi tiết:**

{{detail}}
<!-- /OPTIONAL -->

<!-- OPTIONAL: po_decision -->
**PO decision | Quyết định của PO:** {{po_decision}}
<!-- /OPTIONAL -->
