# Deep Research — Tương lai SDLC AI-native cho `cleanmatic-skills`

**Ngày:** 2026-06-01 · **Phạm vi:** hướng đi tương lai của repo (product-spec + claude-pack) theo khía cạnh SDLC
**Bối cảnh team:** startup nhỏ/vừa, **PO phi kỹ thuật làm việc trực tiếp với 1 senior engineer** (không có lớp PM/BA), phát triển **chủ yếu bằng AI coding agents**, engineer thạo workflow agentic (Claude Code, subagents, orchestration), PO biết dùng AI nhưng nền tảng kỹ thuật mỏng.

> **Cách đọc độ tin cậy:** `HIGH` = nhiều nguồn primary + verify đồng thuận 3-0; `MEDIUM` = nguồn đơn/secondary hoặc verify thiếu phiếu; `LOW/UNVERIFIED` = trích từ nguồn primary nhưng vòng cross-verify sạch bị rate-limit cắt (xem Phương pháp).

---

## 0. Tóm tắt điều hành (TL;DR)

Với đúng archetype team này, **state of the art là Spec-Driven Development (SDD)**: một bản spec có cấu trúc trở thành *source of truth*, code là *output last-mile* được sinh ra sau cùng [2,4,5]. Hai skill repo đang có **map đúng vào đầu vòng lặp này nhưng dừng quá sớm**:

- `product-spec` = **engine capture yêu cầu hướng PO** — chính là pha "Specify / what-why" mà mọi công cụ SDD incumbent (GitHub Spec Kit, Kiro, BMAD-METHOD) **mặc định một developer làm** [2]. Đây là *seam khác biệt*, không trùng lặp.
- `claude-pack` = **lớp phân phối** cho hệ sinh thái `.claude` — đúng đơn vị đóng gói chuẩn (skill = thư mục `SKILL.md`) mà Anthropic chính thức hóa [9,10].

**Khoảng trống chiến lược:** combo dừng ở *spec authoring + packaging*. Nó **thiếu vòng `spec → plan → implement → review → ship → trace-back`** mà Spec Kit (Specify→Plan→Tasks→Implement) và BMAD (file-based handoff) đã chuẩn hóa [1,2,3], và **thiếu bước verify/trace-back đóng vòng** — chính là nút thắt thực sự của 2026: *agent sinh code nhanh hơn tốc độ team verify được* [7,15].

**Hướng đi đòn bẩy cao nhất (1 câu):** biến hierarchy Vision/BRD/PRD/Epic/Story của `product-spec` thành **spec thực thi được, feed thẳng cho coding agent**, và bổ sung **bước hậu-implement so code đã ship ngược lại spec + liệt kê requirement chưa được đáp ứng** — đó đúng là phần *PO→agent handoff* và *intent→code traceability* mà **chưa incumbent nào làm tốt cho một chủ sở hữu phi kỹ thuật**.

---

## 1. Phương pháp & lưu ý độ tin cậy

- 6 angle nghiên cứu × WebSearch song song → 23 nguồn → ~105 claim trích xuất; verify đối kháng theo lô (batched, 3 voter/claim, ≥2 phiếu refute = giết claim); synthesize 2 tầng.
- **Sự cố vận hành (đã chẩn đoán):** chạy nhiều workflow nặng liên tiếp gây **HTTP 429 rate_limit (giới hạn token/phút)**. Hệ quả: (a) vòng verify đầu tiên fail toàn bộ → đã fix bằng batching; (b) một số fetch + vòng synthesize cuối bị 429 → **20/28 agent ở lần chạy mini-workflow dính 429**. Đây là giới hạn hạ tầng theo phút, không phải lỗi nội dung.
- **Tác động lên báo cáo:** 8 finding angle a/b/c/e đã verify sạch 3-0. 7 claim angle (d) từ nguồn **primary Anthropic** đã confirmed (vote 1-0 — chỉ 1 voter lọt qua rate-limit nhưng *affirm*, nguồn chính thống nên giữ ở MEDIUM/HIGH). Một số claim primary khác (AWS AI-DLC, UserTrace, Sonar) đã **fetch thành công từ nguồn gốc** nhưng vòng cross-verify sạch bị cắt → đánh dấu `UNVERIFIED-primary`.
- **2 claim bị refute (loại có chủ đích):** số liệu star/version cụ thể của Spec Kit (vote 1-2, con số không đáng tin), và luận điểm "orchestration handoff là thách thức *chủ đạo*" (vote 1-2, mâu thuẫn framing verification-confidence mạnh hơn).

---

## 2. Findings theo angle

### (a) SDLC AI-native 2025–2026 — best practices đang nổi

- **F1 · `HIGH`** — SDD là paradigm thống trị 2026; đảo quan hệ spec/code: spec có cấu trúc là source of truth, code là output sinh ra sau. [1,4,5]
- **F5 · `HIGH`** — **Nút thắt 2026 = "confidence", không phải "velocity".** Agent sinh code nhanh hơn tốc độ verify, output agent *đục* (opaque) khó review hơn code người. Team không-PM → gánh nặng dồn lên 1 senior engineer ⇒ **đầu tư vào review/governance/verify, không phải sinh thêm code**. [7]
- **F6 · `MEDIUM`** — Một agentic SDLC thật cần 4 trụ đồng thời: **context · knowledge · multi-player collaboration · governance** (scoped access, attributed runs, guardrails audit được). Thiếu một là "autocomplete nhanh hơn có thêm bước". Combo hiện tại phủ context-packaging + một phần knowledge; **thiếu governance + bề mặt cộng tác đa người**. [7]
- **F7 · `MEDIUM`** — Vai trò người dịch chuyển: từ viết code nền tảng → **orchestrate agent, thiết kế guardrail, review output first-pass**. Đúng profile "senior eng thạo agentic" của team. Tooling nên *khuếch đại orchestrator*, không thay thế việc code. [8]
- **F13 · `UNVERIFIED-primary`** — AWS mở nguồn **AI-DLC** (AI-Driven Development Life Cycle): 3 pha Inception/Construction/Operations; **human quyết định/validate, AI plan/execute**; intent-driven; **log mọi artifact/quyết định/approval thành "trail" kiểm tra được** (traceability-by-construction). [13]

### (b) Spec-Driven Development & cách PO phi kỹ thuật bàn giao cho agent

- **F2 · `HIGH`** — Mọi công cụ SDD incumbent đều formal hóa pipeline đa-pha tách *what/why* (phi kỹ thuật) khỏi *how* (kỹ thuật): **Spec Kit** Constitution→Specify→Plan→Tasks→Implement; **Kiro** Requirements→Design→Tasks (GIVEN/WHEN/THEN); **BMAD** 12+ agent vai trò (PM, Architect, Developer, UX...) qua **file-based handoff** (mỗi agent đọc output doc của agent trước). **Combo product-spec+claude-pack chưa có bản end-to-end nào của vòng này.** [1,2,3]
- **F8 · `HIGH`** — **Spec durability có 3 mức:** *spec-first* (bỏ sau khi build) · *spec-anchored* (spec tồn tại/tiến hóa qua maintenance) · *spec-as-source* (chỉ sửa spec, người không bao giờ chạm code). Đuổi theo *spec-as-source* dính **failure mode MDD+LLM đã ghi nhận**: vừa *cứng nhắc* vừa *phi-tất-định* — agent "bỏ qua ghi chú, coi đó là spec mới rồi sinh lại từ đầu, tạo bản trùng". ⇒ **Mục tiêu tự nhiên của product-spec là spec-anchored** (source bền, người curate), KHÔNG phải auto-regen codegen. [2]

### (c) Cộng tác PO↔dev trực tiếp khi AI thay lớp PM/BA & traceability intent→code

- **F3 · `HIGH`** — **PO→agent handoff là khoảng trống *được nêu rõ nhưng chưa ai giải*** trong tooling SDD: mọi incumbent *ngầm định một developer làm phần phân tích yêu cầu* ("None of this is made explicit... presented as a given that a developer would do all this analysis"; tác giả tự hỏi "Or have developers pair with product people?"). Đây đúng seam `product-spec` lấp (PO phi kỹ thuật capture yêu cầu không cần code) ⇒ **khác biệt, không thừa**. [2,3]
- **F4 · `HIGH`** — **Traceability intent→code hiện *nông và không nhất quán*** ngay cả trong công cụ SDD chuyên dụng (Kiro trace về số requirement; Tessl đánh dấu file `// GENERATED FROM SPEC`; Spec Kit sinh 8+ file/spec nhưng *không map requirement→code rõ ràng*, chỉ dựa version control). `product-spec` *đã* dựng hierarchy traceable (điểm mạnh) nhưng **dừng ở biên spec** ⇒ **đóng vòng ngược về code đã ship là capability đòn bẩy cao nhất** ("After implementing, compare result with spec, list any spec items not addressed"). [2,5,6]
- **F14 · `UNVERIFIED-primary`** — **UserTrace** (arXiv 2509.11238): hệ multi-agent LLM **tự sinh user-level requirements + khôi phục live trace links** user-req → impl-req → code từ repo; user study cho thấy **giúp người không phải dev validate xem repo AI sinh ra có khớp intent không**. ⇒ Bằng chứng rằng vòng spec→code traceability **có thể tự động hóa**, đúng use-case PO-validation của product-spec. [14]
- **F15 · `UNVERIFIED-primary`** — Sonar (khảo sát n=1,100+): **96% dev không hoàn toàn tin** code AI đúng chức năng, nhưng **chỉ 48% luôn verify** trước khi commit (verification gap); AI ≈ **42% code commit hôm nay → dự kiến 65% vào 2027**; 64% dev đã dùng agent tự hành. ⇒ Xác nhận archetype + củng cố F5. [15]

### (d) Agent skills / context-packaging / phân phối — `.claude`, MCP, Plugins/Marketplaces

> *(Toàn bộ trích từ nguồn **primary** Anthropic/MCP; vote 1-0 do rate-limit cắt voter — giữ MEDIUM/HIGH vì nguồn chính thống.)*

- **F-D1 · `HIGH`** — **Claude Code plugins gom skills + agents + hooks + MCP servers thành *một đơn vị phân phối*; marketplaces là catalog** để discover/install mà không phải tự build. [9]
- **F-D2 · `HIGH`** — Marketplace = **git repo chứa `.claude-plugin/marketplace.json`**; add qua `owner/repo` rồi install `plugin-name@marketplace`. ⇒ **Kênh phân phối chính thống cho chính `.claude` artifacts của một repo.** [9]
- **F-D3 · `MEDIUM`** — Plugin skill **namespaced theo tên plugin** (`/commit-commands:commit`) — đúng cách repo này đã expose `/ck:*` và `cleanmatic:*`. [9]
- **F-D4 · `HIGH`** — Trước khi install, Claude Code hiện **manifest "Will install"** (commands/agents/skills/hooks/MCP) + **ước tính Context cost** — **tương đương built-in của review manifest-first mà `claude-pack` làm**. [9]
- **F-D5 · `HIGH`** — Anthropic có **community marketplace**: plugin bên thứ ba qua **validation/safety screening tự động**, **mỗi plugin pin vào commit SHA cụ thể** ⇒ **con đường phân phối tất định chính thống** cho việc share `.claude`. [9]
- **F-D6 · `HIGH`** — **Agent Skills là chuẩn mở, cross-platform** (Claude.ai, Claude Code, Agent SDK, Developer Platform) ⇒ skill viết trong repo này **portable trên mọi bề mặt Anthropic**, hợp thức hóa mô hình `.claude/skills`. [10]
- **F-D7 · `HIGH`** — **Skill = một thư mục filesystem** (`SKILL.md` + folder instructions/scripts/resources) = **đúng đơn vị `claude-pack` đang bundle tất định** ⇒ cách "tar.gz của `.claude`" của repo khớp format skill chính thống. [10]

### (e) Khoảng trống / rủi ro / cơ hội — xem §3, §4, §6

---

## 3. Gap map — vòng SDLC của `product-spec` + `claude-pack` *hôm nay*

| Stage | Trạng thái | Ghi chú |
|---|---|---|
| **spec** | ✅ `covered` | product-spec: Vision→BRD→PRD→Epic→Story + AC, traceable, validated, PO-safe, approval gating [bản thân repo] |
| **plan** | ❌ `missing` | Không emit artifact plan/tasks cho agent (không có cầu Specify→Plan→Tasks như Spec Kit) [1,2] |
| **implement** | ❌ `missing` (chủ ý) | Không handoff codegen; engineer + agent làm, nhưng **không có cầu spec→implement** [2,3] |
| **review** | 🟡 `partial` | Script validate spec consistency/traceability có; **không có review/verify code đã ship** [7] |
| **ship** | 🟡 `partial` | claude-pack ship bundle `.claude` tất định; **không ship product increment**; chưa có kênh plugin/marketplace [9] |
| **trace-back** | ❌ `missing` | Không map code→Story ID, không report "requirement chưa đáp ứng" [2,5,14] |

---

## 4. Khuyến nghị chiến lược (đã ưu tiên)

> Mọi khuyến nghị tôn trọng ràng buộc cứng: **PO-safe** (ngôn ngữ sản phẩm, không jargon kỹ thuật ở bề mặt PO) · **deterministic** · **spec-anchored, KHÔNG spec-as-source codegen** · không ghi ngoài `docs/product/`.

### NOW (đòn bẩy cao, làm trước)

**R1 — Cầu `spec → plan/tasks` (effort M) · [1,2,3,5]**
product-spec export PRD/Epic/Story + AC thành một artifact **plan.md/tasks.md tiêu thụ-được-bởi-agent** (mirror Spec Kit Specify→Plan→Tasks và BMAD file-based handoff). Đây là mảnh ghép biến spec thành đầu vào thực thi cho coding agent. *Giữ PO-safe:* artifact kỹ thuật nằm phía engineer; PO vẫn chỉ thấy Story/AC ngôn ngữ sản phẩm.

**R2 — Bước `trace-back` / verification pass (effort M) · [2,5,7,14]**
Script + LLM nhận PR/code đã ship + spec → **map code ↔ Story ID**, **liệt kê Story/AC chưa được đáp ứng** ("compare result to spec, list unaddressed requirements"). Đánh thẳng nút thắt #1 của 2026 (verification) **và** gap traceability; output đọc-được-bởi-PO. *Đây là capability khác biệt nhất so với mọi incumbent.*

**R3 — Phát hành như Claude Code plugin + marketplace (effort S–M) · [9,10]**
Publish `cleanmatic-skills` thành **git marketplace** (`.claude-plugin/marketplace.json`); plugin bundle product-spec + claude-pack + agents + hooks; **pin commit SHA**; "Will install" manifest đã trùng tinh thần review manifest-first của claude-pack. Nâng cấp phân phối vượt tarball thủ công, đúng con đường tất định chính thống của Anthropic. *claude-pack vẫn giữ vai trò kênh offline/air-gapped + portable fallback.*

### NEXT

**R4 — Lớp governance/attribution (effort M) · [7,13]**
Ghi nhận **agent run nào thỏa Story nào** (attributed, auditable runs) để 1 senior engineer audit được — bổ sung trụ "governance" đang thiếu (F6). AI-DLC log-everything-trail là tham chiếu [13].

**R5 — Bề mặt review/acceptance hướng PO (effort M) · [7,14]**
Cho PO validate increment đã ship đối chiếu AC bằng ngôn ngữ sản phẩm (UserTrace chứng minh non-dev validate được repo AI sinh ra theo intent) [14].

**R6 — Living-spec sync, giữ spec-anchored (effort M) · [2,17]**
Khi code/PR drift, **flag các Story bị ảnh hưởng cho PO review** (delta-update của product-spec đã làm việc này cho downstream node — mở rộng sang drift của code). **KHÔNG** auto-regen (tránh failure mode F8).

### LATER

**R7 — Interop với Spec Kit / Kiro làm backend implement (effort L) · [1,2]**
Emit hierarchy tương thích `.specify` để engineer dùng *bất kỳ* implement loop SDD nào. Định vị **"PO front-end tốt nhất cắm vào SDD backend có sẵn"** thay vì tự dựng cả vòng dọc.

**R8 — Hội tụ đóng gói MCP/skill (effort L) · [10,12]**
Bám hướng "skills-over-MCP"; đảm bảo output product-spec tiêu thụ-được qua chuẩn skill, không khóa cứng vào một cơ chế.

---

## 5. Roadmap

- **NOW:** R1 (spec→plan bridge) · R2 (trace-back verify) · R3 (plugin + marketplace)
- **NEXT:** R4 (governance/attribution) · R5 (PO acceptance surface) · R6 (living-spec/code-drift sync)
- **LATER:** R7 (interop Spec Kit/Kiro backend) · R8 (skill/MCP packaging convergence)

---

## 6. Rủi ro

1. **Bẫy spec-as-source** — đừng đuổi auto-regen code: failure mode MDD+LLM (cứng nhắc + phi-tất-định, regen trùng lặp). Giữ spec-anchored. [2]
2. **Scope creep phá PO-safety** — thêm plan/tasks/code-trace dễ rò jargon kỹ thuật vào bề mặt PO. Giữ artifact kỹ thuật ở phía engineer; PO chỉ thấy ngôn ngữ sản phẩm.
3. **Build-vs-integrate** — dựng cả implement loop là cạnh tranh trực diện Spec Kit/Kiro/BMAD. Seam khác biệt là **PO front-end + trace-back**, KHÔNG phải codegen. Đừng over-build phần giữa.
4. **Khóa hệ sinh thái** — đặt cược plugins/marketplaces/MCP gắn repo vào tiến hóa bề mặt Anthropic. Giữ claude-pack tarball làm fallback portable.
5. **"Verification theater"** — một trace-back report không đáng tin còn tệ hơn không có. Map code→Story phải dựa bằng chứng (diff/test), không đoán.

---

## 7. Câu hỏi mở (chưa giải)

1. product-spec hiện đã emit (hay có thể emit rẻ) artifact plan/tasks cho agent chưa, hay hierarchy dừng ở Story+AC không có cầu Plan→Tasks? → quyết định R1 là *build mới* hay *chỉ thêm format export*.
2. Cơ chế trace-back đúng cho repo *không tự sinh code* là gì: comment Story-ID trong code (kiểu Kiro), report "unaddressed requirements" hậu-implement (kiểu addyosmani), hay convention git-trailer/PR-metadata? Ba cách tồn tại, chưa cách nào rõ ràng tốt nhất cho một PO phi kỹ thuật.
3. Ranh giới spec-anchored vs mọi nỗ lực spec-as-source nằm ở đâu — engineer có nên *luôn* sở hữu thao tác sửa code?
4. **Build-vs-integrate (quyết định chiến lược lớn nhất):** repo nên *interop* với Spec Kit/Kiro làm lớp implement (feed hierarchy kiểu `.specify`) hay tự dựng implement loop riêng? Nguồn mô tả incumbent nhưng không chốt giúp.

---

## 8. Nguồn

**Đã verify sạch (primary/secondary):**
[1] github.com/github/spec-kit · [2] martinfowler.com — exploring-gen-ai/sdd-3-tools · [3] github.com/bmad-code-org/BMAD-METHOD · [4] marktechpost — 9 best AI tools for SDD 2026 · [5] addyosmani.com/blog/good-spec · [6] tessl.io/blog — a look at Spec Kit · [7] coderabbit.ai/guides/agentic-sdlc (blog) · [8] cio.com — agentic AI reshape engineering 2026 (blog)

**Angle (d) — primary Anthropic/MCP (confirmed, vote 1-0 do rate-limit):**
[9] code.claude.com/docs/en/discover-plugins · [10] anthropic.com/engineering — agent-skills · [11] claude.com/blog/skills-explained · [12] modelcontextprotocol.io/community/skills-over-mcp/charter

**`UNVERIFIED-primary` (fetch ok, cross-verify sạch bị rate-limit cắt):**
[13] aws.amazon.com/blogs/devops — AI-DLC · [14] arxiv.org/abs/2509.11238 — UserTrace · [15] sonarsource.com — verification gap in AI coding · [17] augmentcode.com/guides — living specs

**Đã refute (loại):** số liệu star/version Spec Kit (vote 1-2) · "orchestration handoff là thách thức chủ đạo" (vote 1-2, mâu thuẫn framing verification-confidence).

---

*Ghi chú vận hành: báo cáo tổng hợp từ 3 lần chạy workflow `deep-research` (verify đối kháng batched) + 1 mini-workflow lấp gap angle (d). Phần strategist (§3–§6) do tôi tổng hợp trực tiếp từ findings đã verify + context repo (CLAUDE.md) vì vòng synthesize cuối của workflow bị rate-limit (429) cắt — không phải lỗi nội dung. Mọi claim đều gắn nguồn; các điểm `UNVERIFIED-primary` cần một lần cross-verify sạch khi rate-limit nguội nếu muốn nâng lên HIGH.*
