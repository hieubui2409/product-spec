"""telemetry_render.py — the NEW gap over human-analyzer (which ships md/json/html):
ascii (terminal one-glance) + mermaid (fenced charts) renderers, plus md. md/json
reuse formatters.py. NO HTML (D4 — avoids vendored-asset / shipped-render coupling).
NO network, NO inlined JS, NO asset reads — pure text only.

Bilingual scaffolding: every FIXED label (headings, banners, column headers, notes,
disclaimers) is localized via the single `_T` dict, selected by `lang` ("vi" default,
matching the skill's Vietnamese-first narration; "en" on `--lang en`). DYNAMIC data
(numbers, skill ids, script paths, chains) stays language-neutral — the LLM narrates
the interpretive prose on top. One dict = one source of truth (DRY); the LLM is NOT
re-implemented here, only the static frame is translated.

Each renderer takes a LIST of lens aggregates (the "overview" composition) and
dispatches per `lens` key in a stable order. Below-gate lenses render a short
"insufficient data" note instead of recommendations. Ships in the release bundle.
"""
from __future__ import annotations

import re

from formatters import markdown_table

_NEVER_USED_CAP = 20

# Localized fixed labels. `{...}` entries are .format templates. Lists are column
# headers / row labels. en is the fallback for any missing key.
_T: dict[str, dict] = {
    "en": {
        "banner": "== TELEMETRY: USAGE & HEALTH ==",
        "gate": "_Insufficient data (not enough data) — raw counts only, no recommendations._",
        "no_lenses": "_No lenses to render._",
        "no_chart": "> No chart-friendly data yet.",
        "lens_error": "⚠ Lens `{lens}` failed: {error}",
        # usage
        "usage_h": "## Skill Usage (last {days} days)\n",
        "usage_total": "Total invocations: **{inv}** across **{used}** skill(s); catalog {cat}.\n",
        "usage_cols": ["#", "Skill", "Count"],
        "usage_tokens": "Tokens",
        "usage_never": "\n**Never used (owned):** {n}",
        "usage_more": " … (+{n} more)",
        "usage_ext": "\n_(+{n} vendored external skills also unused — expected, not prune candidates.)_",
        "a_usage": "USAGE — {inv} invocations, {used} used, {nu} owned never-used{ext}",
        "a_ext": " (+{n} ext)",
        # session
        "session_h": "## Session Shape\n",
        "session_cols": ["Metric", "Value"],
        "session_rows": ["Sessions", "Avg duration (s)", "Median duration (s)",
                         "Files modified (total)", "Subagents (total)"],
        "session_cooc": "\n**Skill co-occurrence:**",
        "session_cooc_cols": ["Pair", "Sessions"],
        "a_session": "SESSIONS — {n} sessions, avg {avg}s, {files} files, {sub} subagents",
        # health
        "health_h": "## Script Health (approx)\n",
        "health_total": "Runs: **{r}**, errors: **{e}** across {s} script(s).\n",
        "health_cols": ["Script", "Runs", "Errors", "Err%", "Avg"],
        "a_health": "HEALTH — {r} runs, {e} errors across {s} scripts",
        # reliability
        "rel_h": "## Subagent Reliability (last {days} days)\n",
        "rel_cols": ["Agent Type", "Total", "Success", "API Err", "Timeout", "Blocked", "Unknown"],
        "rel_failmodes": "\n**Top failure modes:** ",
        "a_rel": "RELIABILITY — {n} subagent runs",
        "a_rel_row": "   {agent}: {ok}% ok (api={api} timeout={to} blocked={bl} unknown={un})",
        # workflow
        "wf_h": "## Workflow Chains (last {days} days, {n} sessions)\n",
        "wf_thin": "_Thin data: {n} < min {m} sessions — observed chains shown, deviation verdicts withheld._\n",
        "wf_common": "**Most common chains:**",
        "wf_cols": ["Chain", "Count"],
        "wf_none": "_No multi-skill chains observed yet._",
        "wf_dev": "\n**Deviations from declared chains:**",
        "wf_declared": "\n**Declared chains (data/skill-chains.yaml):** {n}",
        "a_wf": "WORKFLOW — {n} sessions, {c} chains, {d} deviations",
        # memory
        "mem_h": "## Memory Health — {status} ({n} memories, {issues} issues)\n",
        "mem_readonly": "(read-only)",
        "mem_orphans": "Orphaned files",
        "mem_dead": "Dead index entries",
        "mem_broken": "Broken [[links]]",
        "mem_dupes": "Duplicate names",
        "mem_invalid": "Invalid frontmatter",
        "mem_stale": "Stale (informational)",
        "mem_missing": "missing",
        "mem_invtype": "invalid type",
        "a_mem": "MEMORY — {status}, {n} memories, {issues} issues (orphans={o} dead={d} broken={b})",
        # product memory (docs/product/.memory)
        "pmem_h": "## Product Memory — {status} ({issues} issues)\n",
        "pmem_absent": "_Store absent — no spec memory yet._",
        "pmem_validated": "**Last validated:** {age}",
        "pmem_never": "never",
        "pmem_missing": "Missing state files",
        "pmem_cache": "**Critique cache:** {n} file(s), {bytes} B",
        "pmem_findings": "**Indexed findings:** {n}",
        "a_pmem": "PRODUCT MEMORY — {status}, {issues} issues (validated={age}, cache={cache})",
        # forensics
        "fx_h": "## Session Forensics",
        "fx_none": "_No session transcripts found._",
        "fx_h_count": "## Session Forensics ({n} session(s), {tok} tokens)\n\n",
        "fx_cols": ["Session", "Skills", "Tools", "Subagents", "Tokens", "Dur", "Files"],
        "a_fx": "FORENSICS — {n} session(s), {tok} tokens",
        # validate
        "val_h": "## Effectiveness Proxy — validate-pass (internal quality)\n",
        "val_na": "not available on current data",
        "val_na_reason": "not available on current data (no validate marker, no validate-script runs)",
        "val_pr_none": "n/a (no validate runs in window)",
        "val_cols": ["Metric", "Value"],
        "val_rate": "Validate pass rate",
        "val_last": "Last status",
        "val_runs": "Runs",
        "val_source": "Source",
        "val_disclaimer": "\n_Measures internal spec quality (validate passed) — NOT market/user outcome (E3, deferred)._",
        "a_val": "VALIDATE-PROXY — {pr} (last: {last}) [internal quality, not E3]",
        "a_val_na": "VALIDATE-PROXY — {reason}",
        "a_val_pr_none": "n/a",
        "a_val_pr": "{pr}% pass",
        # mermaid
        "mm_usage_title": "Skill usage",
        "mm_usage_gate": "> Skill usage: insufficient data for a chart (not enough data).",
        "mm_health_title": "Script error-rate (%)",
        "mm_rel_title": "Subagent success-rate (%)",
        "mm_rel_gate": "> Subagent reliability: insufficient data for a chart (not enough data).",
        # artifact_heat
        "heat_h": "## Artifact Edit Frequency (last {days} days)\n",
        "heat_total": "Total edits: **{total}** across **{n}** artifact(s).\n",
        "heat_cols": ["Artifact", "Edits", "Last edit"],
        "heat_none": "_No artifact edits recorded yet._",
        "a_heat": "ARTIFACT HEAT — {total} edits across {n} artifact(s)",
    },
    "vi": {
        "banner": "== TELEMETRY: MỨC DÙNG & SỨC KHỎE ==",
        "gate": "_Chưa đủ dữ liệu — chỉ số liệu thô, không khuyến nghị._",
        "no_lenses": "_Không có lens nào để hiển thị._",
        "no_chart": "> Chưa có dữ liệu phù hợp để vẽ biểu đồ.",
        "lens_error": "⚠ Lens `{lens}` lỗi: {error}",
        # usage
        "usage_h": "## Mức dùng kỹ năng ({days} ngày gần đây)\n",
        "usage_total": "Tổng lượt gọi: **{inv}** trên **{used}** kỹ năng; catalog {cat}.\n",
        "usage_cols": ["#", "Kỹ năng", "Lượt"],
        "usage_tokens": "Tokens",
        "usage_never": "\n**Chưa dùng lần nào (sở hữu):** {n}",
        "usage_more": " … (+{n} nữa)",
        "usage_ext": "\n_(+{n} kỹ năng ngoài (vendored) cũng chưa dùng — bình thường, không phải ứng viên để xóa.)_",
        "a_usage": "MỨC DÙNG — {inv} lượt gọi, {used} đã dùng, {nu} sở hữu chưa dùng{ext}",
        "a_ext": " (+{n} ngoài)",
        # session
        "session_h": "## Phiên làm việc\n",
        "session_cols": ["Chỉ số", "Giá trị"],
        "session_rows": ["Số phiên", "Thời lượng TB (s)", "Thời lượng trung vị (s)",
                         "Tệp đã sửa (tổng)", "Subagent (tổng)"],
        "session_cooc": "\n**Kỹ năng dùng chung phiên:**",
        "session_cooc_cols": ["Cặp", "Số phiên"],
        "a_session": "PHIÊN — {n} phiên, TB {avg}s, {files} tệp, {sub} subagent",
        # health
        "health_h": "## Sức khỏe script (ước lượng)\n",
        "health_total": "Lần chạy: **{r}**, lỗi: **{e}** trên {s} script.\n",
        "health_cols": ["Script", "Chạy", "Lỗi", "Tỷ lệ lỗi", "TB"],
        "a_health": "SỨC KHỎE — {r} lần chạy, {e} lỗi trên {s} script",
        # reliability
        "rel_h": "## Độ tin cậy subagent ({days} ngày gần đây)\n",
        "rel_cols": ["Loại agent", "Tổng", "Thành công", "Lỗi API", "Timeout", "Bị chặn", "Không rõ"],
        "rel_failmodes": "\n**Kiểu lỗi phổ biến:** ",
        "a_rel": "ĐỘ TIN CẬY — {n} lượt chạy subagent",
        "a_rel_row": "   {agent}: {ok}% ok (api={api} timeout={to} chặn={bl} không rõ={un})",
        # workflow
        "wf_h": "## Chuỗi workflow ({days} ngày gần đây, {n} phiên)\n",
        "wf_thin": "_Dữ liệu mỏng: {n} < tối thiểu {m} phiên — chỉ hiện chuỗi quan sát được, chưa kết luận sai lệch._\n",
        "wf_common": "**Chuỗi phổ biến nhất:**",
        "wf_cols": ["Chuỗi", "Số lần"],
        "wf_none": "_Chưa quan sát thấy chuỗi nhiều kỹ năng._",
        "wf_dev": "\n**Sai lệch so với chuỗi khai báo:**",
        "wf_declared": "\n**Số chuỗi khai báo (data/skill-chains.yaml):** {n}",
        "a_wf": "WORKFLOW — {n} phiên, {c} chuỗi, {d} sai lệch",
        # memory
        "mem_h": "## Sức khỏe bộ nhớ — {status} ({n} bộ nhớ, {issues} vấn đề)\n",
        "mem_readonly": "(chỉ đọc)",
        "mem_orphans": "Tệp mồ côi",
        "mem_dead": "Mục index chết",
        "mem_broken": "Liên kết [[hỏng]]",
        "mem_dupes": "Tên trùng",
        "mem_invalid": "Frontmatter không hợp lệ",
        "mem_stale": "Cũ (tham khảo)",
        "mem_missing": "thiếu",
        "mem_invtype": "type sai",
        "a_mem": "BỘ NHỚ — {status}, {n} bộ nhớ, {issues} vấn đề (mồ côi={o} chết={d} hỏng={b})",
        # product memory (docs/product/.memory)
        "pmem_h": "## Bộ nhớ sản phẩm — {status} ({issues} vấn đề)\n",
        "pmem_absent": "_Chưa có store — spec chưa sinh bộ nhớ._",
        "pmem_validated": "**Validate gần nhất:** {age}",
        "pmem_never": "chưa bao giờ",
        "pmem_missing": "Tệp trạng thái thiếu",
        "pmem_cache": "**Cache critique:** {n} tệp, {bytes} B",
        "pmem_findings": "**Findings đã index:** {n}",
        "a_pmem": "BỘ NHỚ SẢN PHẨM — {status}, {issues} vấn đề (validate={age}, cache={cache})",
        # forensics
        "fx_h": "## Phân tích phiên (forensics)",
        "fx_none": "_Không tìm thấy transcript phiên nào._",
        "fx_h_count": "## Phân tích phiên (forensics) ({n} phiên, {tok} tokens)\n\n",
        "fx_cols": ["Phiên", "Kỹ năng", "Tool", "Subagent", "Tokens", "T.lượng", "Tệp"],
        "a_fx": "FORENSICS — {n} phiên, {tok} tokens",
        # validate
        "val_h": "## Proxy hiệu quả — validate-pass (chất lượng nội bộ)\n",
        "val_na": "chưa có dữ liệu",
        "val_na_reason": "chưa có dữ liệu (không có marker validate, không có lần chạy script validate)",
        "val_pr_none": "không có (không có lần validate nào trong cửa sổ)",
        "val_cols": ["Chỉ số", "Giá trị"],
        "val_rate": "Tỷ lệ validate-pass",
        "val_last": "Trạng thái cuối",
        "val_runs": "Số lần",
        "val_source": "Nguồn",
        "val_disclaimer": "\n_Đo chất lượng spec nội bộ (validate đã pass) — KHÔNG phải hiệu quả thị trường/người dùng (E3, hoãn lại)._",
        "a_val": "VALIDATE-PROXY — {pr} (cuối: {last}) [chất lượng nội bộ, không phải E3]",
        "a_val_na": "VALIDATE-PROXY — {reason}",
        "a_val_pr_none": "không có",
        "a_val_pr": "{pr}% pass",
        # mermaid
        "mm_usage_title": "Mức dùng kỹ năng",
        "mm_usage_gate": "> Mức dùng kỹ năng: chưa đủ dữ liệu để vẽ biểu đồ.",
        "mm_health_title": "Tỷ lệ lỗi script (%)",
        "mm_rel_title": "Tỷ lệ thành công subagent (%)",
        "mm_rel_gate": "> Độ tin cậy subagent: chưa đủ dữ liệu để vẽ biểu đồ.",
        # artifact_heat
        "heat_h": "## Tần suất sửa artifact ({days} ngày gần đây)\n",
        "heat_total": "Tổng lần sửa: **{total}** trên **{n}** artifact.\n",
        "heat_cols": ["Artifact", "Số lần sửa", "Lần sửa gần nhất"],
        "heat_none": "_Chưa ghi nhận lần sửa artifact nào._",
        "a_heat": "ARTIFACT HEAT — {total} lần sửa trên {n} artifact",
    },
}


def _t(lang: str, key: str):
    """Localized label; falls back to English for an unknown lang/key."""
    return (_T.get(lang) or _T["en"]).get(key, _T["en"][key])


# Language-neutral reason codes the validate lens emits → localized label key.
# Keeps the prose out of the gathered dict (one home, no EN-in-VI leak).
_REASON_KEYS = {"no_data": "val_na_reason"}


def _reason_label(a: dict, lang: str) -> str:
    """Localize a lens 'unavailable' reason from its language-neutral reason_code;
    fall back to the short val_na label for an unknown/absent code."""
    key = _REASON_KEYS.get(a.get("reason_code"))
    return _t(lang, key) if key else _t(lang, "val_na")


def _fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def _mermaid_escape(label: str) -> str:
    """Make a label safe inside a mermaid quoted string: no double-quotes,
    newlines, or the `:`/`;` that break pie/bar syntax."""
    s = str(label).replace('"', "'").replace("\n", " ")
    s = re.sub(r"[:;#]", "-", s)
    return s.strip() or "?"


# --- markdown sections (one per lens) ---------------------------------------

def _md_usage(a, top, lang):
    def t(k): return _t(lang, k)
    gate = t("gate")
    out = [t("usage_h").format(days=a["days"])]
    if a.get("gated"):
        out.append(gate + "\n")
    out.append(t("usage_total").format(inv=a["total_invocations"], used=a["skills_used"], cat=a["catalog_size"]))
    rows = [r for r in a["rows"] if r["count"] or r["tokens"]]
    if top:
        rows = rows[:top]
    headers = list(t("usage_cols"))
    if a.get("with_tokens"):
        headers.append(t("usage_tokens"))
    trows = []
    for i, r in enumerate(rows, 1):
        row = [str(i), r["skill"], str(r["count"])]
        if a.get("with_tokens"):
            row.append(_fmt_tokens(r["tokens"]))
        trows.append(row)
    out.append(markdown_table(headers, trows))
    nu = a["never_used"]
    out.append(t("usage_never").format(n=len(nu)))
    if nu:
        shown = nu[:_NEVER_USED_CAP]
        more = t("usage_more").format(n=len(nu) - len(shown)) if len(nu) > len(shown) else ""
        out.append(", ".join(shown) + more)
    ext = a.get("never_used_external_count")
    if ext:
        out.append(t("usage_ext").format(n=ext))
    return "\n".join(out)


def _md_session(a, lang):
    def t(k): return _t(lang, k)
    out = [t("session_h")]
    if a.get("gated"):
        out.append(t("gate") + "\n")
    labels = t("session_rows")
    vals = [a["sessions"], a["avg_duration_s"], a["median_duration_s"],
            a["files_modified_total"], a["subagents_total"]]
    out.append(markdown_table(t("session_cols"), [[lbl, str(v)] for lbl, v in zip(labels, vals)]))
    if a["top_cooccurrence"]:
        out += [t("session_cooc"),
                markdown_table(t("session_cooc_cols"), [[p, str(n)] for p, n in a["top_cooccurrence"]])]
    return "\n".join(out)


def _md_health(a, lang):
    def t(k): return _t(lang, k)
    out = [t("health_h")]
    if a.get("gated"):
        out.append(t("gate") + "\n")
    out.append(t("health_total").format(r=a["total_runs"], e=a["total_errors"], s=a["scripts"]))
    rows = [[r["script"], str(r["runs"]), str(r["errors"]), f"{r['error_rate']}%",
             "—" if r["avg_ms"] is None else f"{r['avg_ms']}ms"] for r in a["rows"]]
    out.append(markdown_table(t("health_cols"), rows))
    return "\n".join(out)


def _md_reliability(a, lang):
    def t(k): return _t(lang, k)
    out = [t("rel_h").format(days=a["days"])]
    if a.get("gated"):
        out.append(t("gate") + "\n")
    rows = [[r["agent_type"], str(r["total"]), f"{r['success_rate']}%",
             str(r["api_error"]), str(r["timeout"]), str(r["blocked"]), str(r["unknown"])]
            for r in a["rows"]]
    out.append(markdown_table(t("rel_cols"), rows))
    if a["top_failure_modes"]:
        out.append(t("rel_failmodes") + ", ".join(f"{m} ({n})" for m, n in a["top_failure_modes"]))
    return "\n".join(out)


def _md_workflow(a, lang):
    def t(k): return _t(lang, k)
    out = [t("wf_h").format(days=a["days"], n=a["sessions_analyzed"])]
    if not a["sufficient"]:
        out.append(t("wf_thin").format(n=a["sessions_analyzed"], m=a["min_sessions"]))
    if a["common_chains"]:
        out += [t("wf_common"),
                markdown_table(t("wf_cols"), [[c["chain"], str(c["count"])] for c in a["common_chains"]])]
    else:
        out.append(t("wf_none"))
    if a["sufficient"] and a["deviations"]:
        out += [t("wf_dev"),
                markdown_table(t("wf_cols"), [[d["chain"], str(d["count"])] for d in a["deviations"]])]
    out.append(t("wf_declared").format(n=len(a["declared_chains"])))
    return "\n".join(out)


def _md_memory(a, lang):
    def t(k): return _t(lang, k)
    out = [t("mem_h").format(status=a["status"], n=a["count"], issues=a["issue_count"]),
           f"`{a['memory_dir']}` {t('mem_readonly')}\n"]

    def _sec(title, items):
        out.append(f"**{title}:** {len(items)}")
        if items:
            out.append("- " + "\n- ".join(items))

    _sec(t("mem_orphans"), a["orphans"])
    _sec(t("mem_dead"), a["dead_entries"])
    _sec(t("mem_broken"), [f"{b['from']} → [[{b['to']}]]" for b in a["broken_links"]])
    _sec(t("mem_dupes"), [f"{n}: {', '.join(fs)}" for n, fs in a["duplicates"].items()])
    # invalid_frontmatter counts toward issue_count → must show detail, else a RED
    # driven only by it would show a headline with no explanation.
    _sec(t("mem_invalid"), [
        f"{m['file']} ({t('mem_missing')}: {', '.join(m['missing']) or '—'}"
        + (f"; {t('mem_invtype')}: {m['invalid_type']}" if m.get("invalid_type") else "") + ")"
        for m in a.get("invalid_frontmatter", [])])
    # stale is informational only (NOT in issue_count) — surface for context.
    _sec(t("mem_stale"), [
        f"{m['file']} ({m['type']}, {m['age_days']}d)" for m in a.get("stale", [])])
    return "\n".join(out)


def _md_product_memory(a, lang):
    def t(k): return _t(lang, k)
    out = [t("pmem_h").format(status=a["status"], issues=a["issue_count"]),
           f"`{a['memory_dir']}` {t('mem_readonly')}\n"]
    if not a["present"]:
        out.append(t("pmem_absent"))
        return "\n".join(out)
    age = a["last_validated_age_days"]
    out.append(t("pmem_validated").format(age=(t("pmem_never") if age is None else f"{age}d")))
    if a["missing_files"]:
        out.append(f"**{t('pmem_missing')}:** " + ", ".join(a["missing_files"]))
    out.append(t("pmem_cache").format(n=a["cache_count"], bytes=a["cache_bytes"]))
    out.append(t("pmem_findings").format(n=a["findings_count"]))
    return "\n".join(out)


def _md_forensics(a, lang):
    def t(k): return _t(lang, k)
    if a["count"] == 0:
        return t("fx_h") + "\n\n" + t("fx_none")
    rows = [[p["session"][:8], str(len(p["skills"])), str(p["tool_calls"]),
             str(p["subagents"]), _fmt_tokens(p["total_tokens"]),
             f"{p['duration_s'] // 60}m", str(len(p["files_modified"]))] for p in a["sessions"]]
    return (t("fx_h_count").format(n=a["count"], tok=_fmt_tokens(a["agg_total_tokens"]))
            + markdown_table(t("fx_cols"), rows))


def _md_validate(a, lang):
    def t(k): return _t(lang, k)
    out = [t("val_h")]
    if not a.get("available"):
        out.append(f"_{_reason_label(a, lang)}_")
        return "\n".join(out)
    if a.get("gated"):
        out.append(t("gate") + "\n")
    pr = a["validate_pass_rate"]
    pr_str = t("val_pr_none") if pr is None else f"{pr}%"
    out.append(markdown_table(t("val_cols"),
                              [[t("val_rate"), pr_str],
                               [t("val_last"), str(a["last_status"])],
                               [t("val_runs"), str(a["total"])],
                               [t("val_source"), str(a.get("source", "?"))]]))
    out.append(t("val_disclaimer"))
    return "\n".join(out)


def _md_artifact_heat(a, lang):
    def t(k): return _t(lang, k)
    out = [t("heat_h").format(days=a["days"])]
    rows = a.get("rows", [])
    if not rows:
        out.append(t("heat_none"))
        return "\n".join(out)
    out.append(t("heat_total").format(total=a["total_edits"], n=len(rows)))
    out.append(markdown_table(t("heat_cols"),
                              [[r["artifact"], str(r["edits"]), r.get("last_edit", "")[:10]]
                               for r in rows]))
    return "\n".join(out)


_MD = {
    "usage_tokens": lambda a, top, lang: _md_usage(a, top, lang),
    "session_shape": lambda a, top, lang: _md_session(a, lang),
    "health": lambda a, top, lang: _md_health(a, lang),
    "reliability": lambda a, top, lang: _md_reliability(a, lang),
    "workflow_chains": lambda a, top, lang: _md_workflow(a, lang),
    "memory_health": lambda a, top, lang: _md_memory(a, lang),
    "product_memory": lambda a, top, lang: _md_product_memory(a, lang),
    "forensics": lambda a, top, lang: _md_forensics(a, lang),
    "validate_proxy": lambda a, top, lang: _md_validate(a, lang),
    "artifact_heat": lambda a, top, lang: _md_artifact_heat(a, lang),
}


def render_md(aggregates: list[dict], top=None, lang: str = "vi") -> str:
    parts = []
    for a in aggregates:
        if a.get("error"):  # isolated-lens failure → visible line, never a silent drop
            parts.append(_t(lang, "lens_error").format(lens=a.get("lens"), error=a["error"]))
        elif a.get("lens") in _MD:
            parts.append(_MD[a["lens"]](a, top, lang))
    return "\n\n".join(parts) if parts else _t(lang, "no_lenses")


# --- ascii (terminal one-glance) --------------------------------------------
# ascii reuses the markdown grids (they render fine in a monospace terminal) but
# leads each lens with a traffic-light status line for a quick scan.

def _light(ok: bool) -> str:
    return "[OK]" if ok else "[!]"


def render_ascii(aggregates: list[dict], lang: str = "vi") -> str:
    def t(k): return _t(lang, k)
    lines = [t("banner")]
    for a in aggregates:
        if a.get("error"):  # isolated-lens failure → visible status line, never dropped
            lines.append("\n[!] " + t("lens_error").format(lens=a.get("lens"), error=a["error"]))
            continue
        lens = a.get("lens")
        if lens == "usage_tokens":
            ext = a.get("never_used_external_count", 0)
            ext_s = t("a_ext").format(n=ext) if ext else ""
            lines.append("\n" + _light(not a.get("gated")) + " "
                         + t("a_usage").format(inv=a["total_invocations"], used=a["skills_used"],
                                               nu=len(a["never_used"]), ext=ext_s))
        elif lens == "session_shape":
            lines.append("\n" + _light(not a.get("gated")) + " "
                         + t("a_session").format(n=a["sessions"], avg=a["avg_duration_s"],
                                                 files=a["files_modified_total"], sub=a["subagents_total"]))
        elif lens == "health":
            ok = a["total_errors"] == 0
            lines.append("\n" + _light(ok) + " "
                         + t("a_health").format(r=a["total_runs"], e=a["total_errors"], s=a["scripts"]))
            for r in a["rows"][:10]:
                avg = "—" if r["avg_ms"] is None else f"{r['avg_ms']}ms"
                lines.append(f"   {_light(r['errors'] == 0)} {r['script']}  runs={r['runs']} "
                             f"err={r['errors']}({r['error_rate']}%) avg={avg}")
        elif lens == "reliability":
            lines.append("\n" + _light(not a.get("gated")) + " " + t("a_rel").format(n=a["total"]))
            for r in a["rows"][:10]:
                lines.append(t("a_rel_row").format(agent=r["agent_type"], ok=r["success_rate"],
                                                   api=r["api_error"], to=r["timeout"],
                                                   bl=r["blocked"], un=r["unknown"]))
        elif lens == "workflow_chains":
            lines.append("\n" + _light(a["sufficient"]) + " "
                         + t("a_wf").format(n=a["sessions_analyzed"], c=len(a["common_chains"]),
                                            d=len(a["deviations"])))
        elif lens == "memory_health":
            lines.append("\n" + _light(a["status"] == "GREEN") + " "
                         + t("a_mem").format(status=a["status"], n=a["count"], issues=a["issue_count"],
                                             o=len(a["orphans"]), d=len(a["dead_entries"]),
                                             b=len(a["broken_links"])))
        elif lens == "product_memory":
            age = a["last_validated_age_days"]
            age_s = t("pmem_never") if age is None else f"{age}d"
            lines.append("\n" + _light(a["status"] == "GREEN") + " "
                         + t("a_pmem").format(status=a["status"], issues=a["issue_count"],
                                              age=age_s, cache=a["cache_count"]))
        elif lens == "forensics":
            lines.append("\n[i] " + t("a_fx").format(n=a["count"], tok=_fmt_tokens(a["agg_total_tokens"])))
        elif lens == "validate_proxy":
            if a.get("available"):
                pr = a["validate_pass_rate"]
                pr_str = t("a_val_pr_none") if pr is None else t("a_val_pr").format(pr=pr)
                lines.append("\n" + _light(not a.get("gated")) + " "
                             + t("a_val").format(pr=pr_str, last=a["last_status"]))
            else:
                lines.append("\n[i] " + t("a_val_na").format(reason=_reason_label(a, lang)))
        elif lens == "artifact_heat":
            lines.append("\n[i] " + t("a_heat").format(
                total=a.get("total_edits", 0), n=len(a.get("rows", []))))
    return "\n".join(lines)


# --- mermaid (fenced charts; only chart-friendly lenses) --------------------

def _mermaid_pie(title: str, items: list[tuple]) -> str:
    rows = [f'    "{_mermaid_escape(k)}" : {v}' for k, v in items if v]
    if not rows:
        return ""
    return "```mermaid\npie showData\n    title " + _mermaid_escape(title) + "\n" + "\n".join(rows) + "\n```"


def _mermaid_bar(title: str, items: list[tuple]) -> str:
    """xychart-beta bar; falls back cleanly when empty."""
    items = [(k, v) for k, v in items]
    if not items:
        return ""
    labels = ", ".join(f'"{_mermaid_escape(k)}"' for k, _ in items)
    vals = ", ".join(str(v) for _, v in items)
    return ("```mermaid\nxychart-beta\n    title \"" + _mermaid_escape(title) + "\"\n"
            f"    x-axis [{labels}]\n    bar [{vals}]\n```")


def render_mermaid(aggregates: list[dict], lang: str = "vi") -> str:
    def t(k): return _t(lang, k)
    blocks = []
    for a in aggregates:
        if a.get("error"):  # never silently drop an errored lens, even on the chart surface
            blocks.append(t("lens_error").format(lens=a.get("lens"), error=a["error"]))
            continue
        lens = a.get("lens")
        if lens == "usage_tokens":
            if a.get("gated"):
                blocks.append(t("mm_usage_gate"))
                continue
            items = [(r["skill"], r["count"]) for r in a["rows"] if r["count"]]
            blk = _mermaid_pie(t("mm_usage_title"), items)
            if blk:
                blocks.append(blk)
        elif lens == "health":
            items = [(r["script"].split("/")[-1], r["error_rate"]) for r in a["rows"]]
            blk = _mermaid_bar(t("mm_health_title"), items)
            if blk:
                blocks.append(blk)
        elif lens == "reliability":
            if a.get("gated"):
                blocks.append(t("mm_rel_gate"))
                continue
            items = [(r["agent_type"], r["success_rate"]) for r in a["rows"]]
            blk = _mermaid_bar(t("mm_rel_title"), items)
            if blk:
                blocks.append(blk)
    return "\n\n".join(blocks) if blocks else t("no_chart")


# overview is just the ordered composition the CLI already passes in.
def render_overview(aggregates: list[dict], fmt: str = "md", top=None, lang: str = "vi") -> str:
    if fmt == "ascii":
        return render_ascii(aggregates, lang=lang)
    if fmt == "mermaid":
        return render_mermaid(aggregates, lang=lang)
    return render_md(aggregates, top=top, lang=lang)
