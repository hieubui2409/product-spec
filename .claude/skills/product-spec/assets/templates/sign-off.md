<!--
TEMPLATE: sign-off.md — fragment appended to an artifact body when `--approve` runs.
Also adds the `approval:` block to the artifact frontmatter (handled by generate_templates.py).
-->

---

## Sign-Off | Phê duyệt

| Field | Value | Trường | Giá trị |
|-------|-------|--------|---------|
| Artifact | {{artifact_id}} | Tài liệu | {{artifact_id}} |
| Approved by | {{approved_by}} | Phê duyệt bởi | {{approved_by}} |
| Approved at | {{approved_at}} | Phê duyệt ngày | {{approved_at}} |
| Approved version | {{approved_version}} | Phiên bản phê duyệt | {{approved_version}} |
| Stakeholders | {{stakeholders}} | Bên liên quan | {{stakeholders}} |

<!-- OPTIONAL: notes -->
**Notes | Ghi chú:** {{approval_notes}}
<!-- /OPTIONAL -->

> Open issues at approval time (warn-not-block): {{open_issues_at_approval}}
> Vấn đề còn để mở khi phê duyệt (cảnh báo, không chặn): {{open_issues_at_approval}}
