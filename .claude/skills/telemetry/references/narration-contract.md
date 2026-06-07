# Narration Contract — cleanmatic:telemetry

How the skill turns the script's aggregate dicts into a plain-Vietnamese read for a
non-technical product owner. The script gathers; this contract governs the words.

## Voice

- **Vietnamese by default**, native quality: full diacritics, natural register, short
  sentences. Switch to English only on `--en` or an explicit request.
- Talk in **owner language** (skills, work, "lần dùng", "chạy lỗi", "chậm"), not engineering
  jargon. Numbers stay numbers; skill ids / script paths stay ascii.
- **No hype.** This is a status read, not a pitch.

## Structure of a default report (`--lens all`)

1. **Tóm tắt 2–3 dòng** — the headline: how much was used, anything unhealthy, whether
   there's enough data at all.
2. **Mức dùng (Usage)** — top skills + token weight (ước lượng), never-used. **Chỉ liệt kê never-used cho skill PO sở hữu (`cleanmatic:*`)** — các skill ngoài (`ck:*`/`com:*`…) chưa dùng là chuyện bình thường (PO không tự viết, không phải ứng viên để xóa); chỉ nêu số lượng external nếu cần, không liệt kê từng cái.
3. **Sức khỏe (Health)** — scripts that error or run slow (approx), subagent reliability.
4. **Phiên làm việc (Sessions)** — count, duration, co-occurrence — only if not gated.
5. **Workflow chains** — only when ≥ min sessions; otherwise say it's too thin.
6. **Validate proxy** — internal quality only; ALWAYS tagged "không phải E3".
7. **Bộ nhớ (Memory)** — orphans/dead/broken links, read-only.
8. **Cái này KHÔNG đo được** — the mandatory honesty section (below).

## MEASURED vs NOT-MEASURED

| MEASURED (report these) | NOT-MEASURED (must disclaim) |
|-------------------------|------------------------------|
| invocation counts, never-used | whether a skill is *valuable* |
| per-skill tokens (ước lượng) | exact billing cost |
| script error-rate, avg ms (approx) | root cause of an error |
| subagent outcome mix | why a subagent failed (unless transcript said) |
| validate-pass (spec well-formed) | **market / user outcome (E3)** |
| memory tidiness | whether a memory is *correct* |

## The honesty gate (hard requirement)

Every report ENDS with **"Cái này KHÔNG đo được"** that names, at minimum:

- **Hiệu quả thị trường / người dùng (E3)** — telemetry cannot see adoption, revenue, or
  user satisfaction. The validate proxy is internal quality only.
- **Mọi lens đang trống / dưới ngưỡng** → state "chưa đủ dữ liệu", do NOT infer a trend.
- **Các số ước lượng** (tokens, ms, exit) → label as directional, not exact.

If the whole repo is thin (most lenses gated), the report LEADS with "chưa đủ dữ liệu để
kết luận" rather than dressing up a handful of points as insight.

## Recommendations

- Always **gợi ý**, never an order. Example: "Gợi ý: skill X chưa dùng lần nào trong 30 ngày —
  cân nhắc xem có cần giữ không." The PO decides.
- **Never** propose to delete skills, edit memory, or change scope — the skill is read-only and
  has no such authority.
- Suppress recommendations entirely for any **gated** lens.

## Tone examples

- Good: "Trong 30 ngày, `product-spec` được dùng 8 lần (nhiều nhất), tốn ~450K tokens (ước lượng).
  3 skill chưa dùng lần nào."
- Good: "Chưa đủ dữ liệu về subagent (mới 3 lần chạy) — chưa kết luận được độ tin cậy."
- Bad: "Skill X là skill hiệu quả nhất." (hiệu quả is not measured — usage ≠ value.)
- Bad: "Validate pass 100% nên sản phẩm sẽ thành công." (conflates internal quality with E3.)
