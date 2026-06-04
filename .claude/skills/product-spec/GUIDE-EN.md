# `product-spec` Guide for Product Owners

> This guide is for the **Product Owner (PO)** — the person who owns the product, with no coding required.
> You'll learn how to use the `product-spec` skill to turn the ideas in your head into a coherent, fully
> traceable set of product documents, without writing a single line of code.
>
> Vietnamese version: [`GUIDE-VI.md`](./GUIDE-VI.md).

---

## 1. What does this skill do for you?

Picture this: you've just had a product idea. Your head is full of it — the problem you want to solve, who
the customers are, the features to build, what comes first. But it's all scattered across notes, meetings,
and different Google Docs.

`product-spec` helps you **gather it all into one ordered document tree**:

```
Vision
   └── 1 Business Requirements Document (BRD)
          └── many feature documents (PRDs)
                 └── large work groups (Epics)
                        └── user stories (Stories) with acceptance criteria
```

Each layer links to the one above it through an identifier, so you can always answer *"Which business goal
does this story serve?"* or *"Does this goal have any feature carrying it yet?"*.

The key thing to remember: **you talk to the skill in plain product language.** You describe what you want,
the skill interviews you with a few questions, then generates the documents. You never need to memorize any
technical commands.

---

## 2. Two ways to give instructions — and which to prefer

There are two ways to ask the skill to work. **The preferred way is the first — speaking in natural language.**

### Way 1 (preferred): Speak in natural language

Just describe what you want, as if talking to a product assistant:

> *"I want to start writing the spec for a new product."*
>
> *"Help me add a payment feature to the product."*
>
> *"Check whether my current set of documents is missing anything."*

The skill figures out your intent and runs the right workflow. This is the most natural way and the one we
recommend, because you don't have to remember anything.

### Way 2 (equivalent): Type a "flag"

If you're already comfortable and want to go straight to work, every action has a short equivalent "flag".
For example:

```
/cleanmatic:product-spec --validate
```

The two ways produce **exactly the same result**. Flags are just a shortcut for people who already know the
ropes. Throughout this guide, every scenario lists both ways so you can compare.

> 💡 **Tip:** If you're not sure what to do, just type `/cleanmatic:product-spec` (with nothing else). The
> skill looks at the current state of your documents and shows a **menu** of sensible next actions.

---

## 3. Every use case — ordered by priority

Below is everything the skill can do, ordered **from what you need first to what comes later**. Each scenario
includes: when to use it, a full **sample conversation**, and the equivalent flag command.

All examples use a real product from the skill's sample set: **Acme Shop** — a web storefront for small
boutique fashion brands, helping them sell directly to fans without a middleman marketplace.

---

### Priority 1 — Start a new product from zero

**When to use:** You're starting completely fresh, with no documents yet.

This is always the first step. The skill walks you through a short interview about the product vision: the
problem you solve, your target customers (called *personas*), the core value, and the 1–3 year direction.

#### Conversation

> **You:** I want to start writing the product spec for a web storefront serving small boutique fashion brands.
>
> **Skill:** Great, let's start with the vision. First, what *problem* does this product solve, and for whom?
>
> **You:** Boutique brands have to sell through big marketplaces that take 30%+ commission and bury them
> among competitors. Fans want to support them directly but have no easy path.
>
> **Skill:** Clear. So we have at least two user groups: the shopper and the store-admin. Correct? And what's
> the *core value* — the one-line version — of the product?
>
> **You:** Correct. Core value: help boutique brands sell directly to fans, without middlemen.
>
> **Skill:** And the *north-star metric* — the single most important number you're chasing?
>
> **You:** Repeat-purchase rate per brand.
>
> **Skill:** That's enough to build the vision. I'll create two files: `PRODUCT.md` (concise product facts)
> and `vision.md` (the vision narrative). Review them and tweak as needed.

After this step, you have a `docs/product/` folder with your first `PRODUCT.md` and `vision.md`.

> 💡 **Have raw material already?** If you have interview transcripts, support-ticket dumps, or competitor
> notes (as `.md`/`.txt` files), point the skill at them with **`--discover`** to *seed* this interview with
> **candidate** personas and problems instead of starting cold. It reads only the files you name (fenced to
> your project, dotfiles like `.env` skipped, directories walked within a safe limit), proposes candidates,
> and **confirms each with you before anything is written** — it never auto-creates a persona.
>
> > **You:** Discover personas from `research/interviews/`.
> >
> > **Skill:** I read 3 `.md` files. Candidate personas I'm proposing (confirm / edit / reject each):
> > "province shopper who finds the local pool empty", "returnee who wants depth over small talk"…

#### Equivalent flag

```
/cleanmatic:product-spec                # no flag → skill sees nothing exists → offers to initialize
/cleanmatic:product-spec --product      # go straight to creating/refreshing PRODUCT.md
/cleanmatic:product-spec --discover research/interviews/   # seed the interview from raw files/dirs
```

---

### Priority 2 — Dump a "brain-dump" and let the skill organize it

**When to use:** You already have a lot of ideas written messily (from meeting notes, brainstorms) and want
the skill to **automatically decompose** them into business goals, features, epics, and stories.

This is the biggest time-saver. You paste a long passage, the skill breaks it into structure and **asks you
back at any ambiguous split** before committing.

#### Conversation

> **You:** I have a pile of notes, help me organize them: *"Shoppers need to add items to cart, then check
> out on a single page with address and card. Pay via Stripe. Send an order confirmation email. Returning
> shoppers should have saved addresses. Business goals: onboard 100 brands in 12 months and reach 80%
> 90-day repeat-purchase rate."*
>
> **Skill:** I read two *business goals*:
> - BRD-G1 — Onboard 100 boutique brands in 12 months.
> - BRD-G2 — Achieve 80% 90-day repeat-purchase rate.
>
> And one large *feature area*: **Checkout**. Within it, I see two possible work groups:
> 1. Sign-in + address entry.
> 2. Stripe payment + order confirmation.
>
> Do you want me to split it into two epics like that, or keep it as one?
>
> **You:** Split into two, because payment depends on sign-in.
>
> **Skill:** Makes sense. I'll create the "Checkout" PRD, epic E1 (Sign-in + Address), epic E2 (Stripe
> Payment, depends on E1), plus the matching stories. I'll show you each batch for approval before writing.

The skill **never commits** ambiguous splits on its own — it always confirms with you batch by batch.

#### Equivalent flag

```
/cleanmatic:product-spec --auto
```

---

### Priority 3 — Write the business goals document (BRD)

**When to use:** You want to capture the **business goals**, success metrics, stakeholders, constraints, and
competitive landscape. Each product has exactly **one** BRD.

#### Conversation

> **You:** Help me write the business goals document for Acme Shop.
>
> **Skill:** We already have two goals from earlier (onboard 100 brands; 80% 90-day repeat). Do you want to
> add concrete *success metrics* for each?
>
> **You:** Yes: `brands-onboarded` target 100, and `repeat-rate-90d` target 80%.
>
> **Skill:** What about *stakeholders* and *constraints*?
>
> **You:** Stakeholders: founders, lead engineer, 5 design-partner brands. Constraints: Q3 launch deadline,
> ~$300K seed budget.
>
> **Skill:** And the *competitive landscape* — who are the competitors?
>
> **You:** Shopify (high threat) and Big Cartel (medium).
>
> **Skill:** That's enough. I'll write `brd.md`, declaring competitors once here so later PRDs reference them
> by ID (COMP-SHOPIFY, COMP-BIGCARTEL) — avoiding duplicated information.

#### Equivalent flag

```
/cleanmatic:product-spec --brd
```

---

### Priority 4 — Add a feature area (PRD)

**When to use:** You want to describe **one feature area** in detail — e.g. "Checkout", "Search", "Accounts".
Each feature area is its own PRD. A product has many PRDs.

A PRD is where you define: which business goal this feature serves, which persona it's for, the functional
requirements (ordered by **MoSCoW**: Must / Should / Could / Won't this round), non-functional requirements,
risks, and how it stacks up against competitors.

#### Conversation

> **You:** Add a payment feature for me.
>
> **Skill:** Which business goal does this "Checkout" feature serve?
>
> **You:** Both BRD-G1 and BRD-G2 — with payment, brands can ship orders and customers can buy again.
>
> **Skill:** Which persona, and what priority?
>
> **You:** The *shopper* persona. This is a *Must-have*, part of the core value, to do *now*.
>
> **Skill:** Let's list requirements by MoSCoW. What's in *Must*?
>
> **You:** Cart with add/remove/quantity; single-page checkout form; pay via Stripe; order confirmation email.
>
> **Skill:** *Should* / *Could* / *Won't this round*?
>
> **You:** Should: saved addresses for returning shoppers. Could: Apple/Google Pay. Won't: multi-currency.
>
> **Skill:** Any *risks* to record?
>
> **You:** Yes. Stripe KYC verification delays could block launch (high impact). And a long single-page form
> on mobile risks cart abandonment (medium impact).
>
> **Skill:** I'll write the PRD `prds/checkout.md` as `PRD-CHECKOUT`, target date 2026-09-30, with a risk
> register and a competitive parity table (behind Shopify on ecosystem, at parity with Big Cartel on simplicity).

#### Equivalent flag

```
/cleanmatic:product-spec --prd checkout
/cleanmatic:product-spec --prd            # skill will ask for the feature-area name
```

---

### Priority 5 — Add a large work group (Epic)

**When to use:** A PRD is usually big and needs to be split into a few **epics** — large work groups, each
producing a clear outcome.

#### Conversation

> **You:** In the payment PRD, split out the sign-in and address part into one epic.
>
> **Skill:** What's the goal of this epic, and how is it measured?
>
> **You:** Goal: shoppers sign in (via magic-link) and enter a delivery address, ready to pay. Criteria:
> sign-in success rate above 90%, address-step completion above 80%.
>
> **Skill:** Any risk specific to this epic?
>
> **You:** Magic-link emails could land in spam, blocking sign-in. Medium impact.
>
> **Skill:** I'll create epic `PRD-CHECKOUT-E1` (Sign-in + Address), target date 2026-08-15. Payment and
> confirmation will be the follow-on epic `PRD-CHECKOUT-E2`, depending on this one.

#### Equivalent flag

```
/cleanmatic:product-spec --epic PRD-CHECKOUT
/cleanmatic:product-spec --epic           # skill will ask which PRD this epic belongs to
```

---

### Priority 6 — Add a user story with acceptance criteria

**When to use:** You split an epic into **stories** — the smallest unit, told from the user's point of view,
with clear **acceptance criteria** that define when it's "done".

A story is the only place that holds acceptance criteria (the PRD never duplicates them). Each story carries
a relative size: `S` / `M` / `L` — **never** story points or hours.

#### Conversation

> **You:** Add the magic-link sign-in story at the checkout step.
>
> **Skill:** State it in the "As a… I want… so that…" form.
>
> **You:** As a shopper, I want to sign in via a magic link at checkout, so that I don't have to remember a
> password and can complete my purchase quickly.
>
> **Skill:** What are the acceptance criteria? (Each one should be in the "Given… when… then…" form.)
>
> **You:**
> 1. Given a shopper at checkout, when they enter a valid email, then a magic-link sign-in email is sent
>    within 30 seconds.
> 2. Given a shopper who clicked the magic link, when they return to the tab, then their cart is preserved
>    and the checkout form is pre-filled with any saved address.
>
> **Skill:** Estimated size?
>
> **You:** Size M.
>
> **Skill:** I'll write story `PRD-CHECKOUT-E1-S1` with those two acceptance criteria.

#### Equivalent flag

```
/cleanmatic:product-spec --story PRD-CHECKOUT-E1
/cleanmatic:product-spec --story          # skill will ask which epic this story belongs to
```

---

### Priority 7 — Check the quality of the document set (Validate)

**When to use:** Any time you want to know whether the set is "healthy": any orphan story (not attached to an
epic)? any broken link? any business goal with no feature carrying it? are stories well-written per the INVEST
principle? anything drifting from the core value, or contradicting an already-locked decision?

The skill runs **two layers**: a machine layer checking structure (orphans, broken links, missing acceptance
criteria, duplicate IDs, **and any business goal with no success metric**), and a judgment layer (story
quality, vagueness, value drift, semantic duplication). The result is an **easy-to-read report**.

> 💡 New check — **every BRD goal must carry at least one success metric.** A goal with an empty or missing
> `metrics` is flagged as an error (a goal you can't measure can't be graded), so it surfaces in the report
> and blocks under `--strict`.

#### Conversation

> **You:** Check my current document set for anything that needs fixing.
>
> **Skill:** I've scanned it. Summary:
> - ✅ Traceability: every story attaches to an epic, every epic to a PRD, every PRD to a goal. No orphans.
> - ⚠️ Warning: epic `PRD-CHECKOUT-E1` is in *draft* while its parent PRD is *approved* — do you want to
>   raise the epic's status?
> - 💡 Quality note: story `PRD-CHECKOUT-E2-S1` is well-written per INVEST, with measurable acceptance
>   criteria. No core-value drift detected.
>
> Do you want me to tighten it up (every warning blocks), or just list them for you to decide?
>
> **You:** Just list them.

> ⚠️ **Important — the skill never auto-reverses an approved decision.** If new information contradicts a
> document already in *approved* status, the skill surfaces it clearly and gives you three choices: **Keep**
> the old version, **Change** to the new one (and re-approve), or **Hybrid** (record both, plan a follow-up).

#### Equivalent flag

```
/cleanmatic:product-spec --validate
/cleanmatic:product-spec --validate --strict   # errors BLOCK the action (use before sign-off)
```

---

### Priority 8 — Apply a change without losing prior work (Update)

**When to use:** Something changed — a goal, a scope, a decision — and you want to update it **without
overwriting** the prose you carefully wrote.

The skill asks what changed, computes the downstream parts that are **affected**, then **flags them for your
review** — rather than rewriting them. Regeneration is optional, opt-in per item.

#### Conversation

> **You:** The checkout launch date moves from Sep 30 to Oct 15. Update it for me.
>
> **Skill:** This change touches the PRD `PRD-CHECKOUT` (target date) and may affect the two child epics
> E1, E2 scheduled earlier. I'll:
> - Update the PRD's target date.
> - **Flag** E1 and E2 for you to review the schedule — I will *not* rewrite the descriptions you wrote.
> - Append a line to the change log (`change-log.md`).
>
> Do you want me to regenerate the schedule paragraph in each epic, or will you edit them yourself?
>
> **You:** I'll edit E1 myself, but have the skill regenerate E2.

#### Equivalent flag

```
/cleanmatic:product-spec --update
```

---

### Priority 9 — Sign off / lock a document (Approve)

**When to use:** A BRD/PRD/Epic/Story is mature and you want to **stamp approval** — record the approver and
date, and flip the status to `approved`.

Before stamping, the skill runs checks (warnings notify but don't block), then records the owner + date. The
skill **never** sets `approved` unless you ask to approve and provide an owner + date.

#### Conversation

> **You:** I want to sign off the payment PRD.
>
> **Skill:** I'll run a quick check first. There's one warning: the two child epics are still in *draft*.
> That warning doesn't block approving the PRD. Confirm approval? Who is the approver and on what date?
>
> **You:** Approver: Jane Doe, today's date. Confirm approval.
>
> **Skill:** Recorded `owner: Jane Doe`, the approval date, and flipped `status: approved` for `PRD-CHECKOUT`.

#### Equivalent flag

```
/cleanmatic:product-spec --approve
```

---

### Priority 10 — Get a 1-page summary for leadership (Summary)

**When to use:** You need a **one-page summary** to send to investors, leadership, or partners — capturing
the vision, goals, scope, and progress.

#### Conversation

> **You:** Create a one-page summary of Acme Shop to send to investors.
>
> **Skill:** I'll synthesize from the vision, BRD, and PRDs into `exec-summary.md`: core value, the two
> business goals with metrics, the feature area in progress (Checkout, Q3 deadline), and the competitive
> landscape. Do you want plain markdown or also a print-ready HTML version?
>
> **You:** Both.

> 💡 **Pick the audience.** The same `--summary` can speak to two audiences: the default **exec one-pager**,
> or a **release-notes** brief — "what changed since the last sign-off" — pulled from the audit trail (below).
> Say "give me release notes since the last approval" or use `--audience release-notes`.

#### Equivalent flag

```
/cleanmatic:product-spec --summary                          # exec one-pager (default)
/cleanmatic:product-spec --summary --audience exec          # same, explicit
/cleanmatic:product-spec --summary --audience release-notes # what changed since last approved
```

---

### Priority 11 — Draw the document set as visuals (Visualize)

**When to use:** You want to *see* the document set instead of reading each file — the traceability tree, a
timeline roadmap, a kanban board, a risk grid, a competitor matrix…

The skill has many "views". Each view renders in one of three forms: **ASCII** (plain text, viewable right in
the chat window), **Mermaid** (a diagram inside markdown), or **HTML** (a polished file that opens directly
in a browser, no server needed).

The main views:

| You want to see… | View name |
|---|---|
| The full traceability tree (goal → PRD → epic → story) | `tree` |
| The timeline roadmap (Now / Next / Later) | `roadmap`, `time` |
| A kanban board grouped by status / horizon / priority | `board` |
| A three-mode explorer (Tree / Flat-tabs / Table-tree) | `explorer` |
| Goal coverage and remaining gaps | `gap`, `heatmap` |
| Priority by MoSCoW (Must/Should/Could/Won't) | `moscow` |
| A risk grid (impact × likelihood) | `risk` |
| A competitor matrix + threat heatmap | `competition` |
| A multi-dimensional summary on one page | `dashboard` |
| Maps by persona, scope, or change vs an old baseline | `persona`, `scope`, `delta` |
| A governance **audit trail** — when · what · who-approved · what-drifted · which decision | `audit` |

#### Conversation

> **You:** Show me the traceability tree for Acme Shop.
>
> **Skill:** Here's the `tree` view in text form:
> ```
> [goal:BRD-G1] Onboard 100 boutique brands · approved
>   [prd:PRD-CHECKOUT] Checkout PRD · approved
>     [epic:PRD-CHECKOUT-E1] Sign-In + Address · draft
>       [story:PRD-CHECKOUT-E1-S1] Magic-link sign-in · draft
>     [epic:PRD-CHECKOUT-E2] Stripe Payment · draft
>       [story:PRD-CHECKOUT-E2-S1] Pay with Stripe · draft
> ```
> Want a polished HTML version to share?
>
> **You:** Yes, and give me the kanban board by status too.
>
> **Skill:** I've written two HTML files into `docs/product/visuals/`: a traceability tree and a kanban
> board grouped by status. Open them directly in a browser — they have a search box and filters; click a
> card to view details.

#### Equivalent flag

```
/cleanmatic:product-spec --viz tree
/cleanmatic:product-spec --viz tree --format html
/cleanmatic:product-spec --viz board --group-by status
/cleanmatic:product-spec --viz roadmap
/cleanmatic:product-spec --viz risk
/cleanmatic:product-spec --viz competition
/cleanmatic:product-spec --viz dashboard
/cleanmatic:product-spec --viz explorer
/cleanmatic:product-spec --viz audit                 # governance audit trail (text, default)
/cleanmatic:product-spec --viz audit --format md     # markdown table (paste into a PR / doc)
/cleanmatic:product-spec --viz audit --format html   # self-contained HTML page (opens in a browser)
```

> 💡 The **`audit`** view is read-only and renders as plain text (default), markdown, or a self-contained
> HTML page — every value is safety-escaped, so even a sign-off name containing odd characters can't break
> the page. It joins your change-log, sign-offs, stale approvals, and decisions into one timeline. If a
> sign-off has no matching change-log entry or decision, it shows up as an explicit **`unreconciled`** row
> rather than being hidden — so a governance gap is never silently swept under the rug.

> 💡 Want to hide deferred items (marked "won't do")? Add "hide the deferred items" — equivalent to the
> `--filter-wont` flag.

---

### Priority 12 — Export a read-once document to share (Export)

**When to use:** You want to bundle a slice of the document set into **one self-contained file** to send to
someone — without making them open each file.

You choose the whole thing or one branch (by ID), pick the layers to include, the level of detail, and the
format (markdown or print-ready HTML).

#### Conversation

> **You:** Export the entire payment branch into one document to send to the design team.
>
> **Skill:** I'll gather the Checkout PRD with its child epics and stories into one self-contained file in
> `docs/product/exports/`. What detail level do you want: *brief* (titles + summaries only), *context*
> (with context), or *full*? And markdown or print-ready HTML?
>
> **You:** Context level, print-ready HTML.

#### Equivalent flag

```
/cleanmatic:product-spec --export PRD-CHECKOUT --format html
/cleanmatic:product-spec --export all                       # export everything
/cleanmatic:product-spec --export PRD-CHECKOUT --layers prd,epic,story --depth full
```

---

### Priority 13 — Work in Vietnamese (or English)

**When to use:** You want the interview and the content written in Vietnamese (or English).

The skill is bilingual. When you choose Vietnamese, the interview questions, vision narrative, story
descriptions, acceptance criteria, and visualization labels are all in Vietnamese. Only the **identifiers**
(`BRD-G1`, `PRD-CHECKOUT`) and the **structural keys** (`personas`, `scope`, `moscow`…) stay in English so
the structure remains stable and shared across both languages.

#### Conversation

> **You:** From now on, interview me and write the documents in Vietnamese.
>
> **Skill:** Switched to Vietnamese. IDs like `PRD-CHECKOUT` and structural labels stay in English for
> consistency; everything else I'll write in natural Vietnamese.

#### Equivalent flag

```
/cleanmatic:product-spec --lang vi
/cleanmatic:product-spec --lang en
```

---

### Priority 14 — Ask "what should I do next?" (Status)

**When to use:** You come back after a break and want a quick health pulse — what changed since the last quality
check, what's still in draft, what hasn't been validated yet. A read-only nudge; it never edits anything.

The skill compares the current document set against the last time you ran a validation and tells you what drifted,
what's unvalidated, and what's still a draft — so you know where to point your attention. It does not re-run the full
quality check (that's Validate); it just reads the last-validated marker and reports.

#### Conversation

> **You:** What's the state of my spec — anything I should look at?
>
> **Skill:** Quick status (read-only, nothing changed):
> - 🕒 3 items changed since your last validation (`PRD-CHECKOUT`, `PRD-CHECKOUT-E1`, story `…-S2`) — worth re-validating.
> - 📝 2 still in *draft*: `PRD-SEARCH`, epic `PRD-SEARCH-E1`.
> - ✅ Everything else matches the last validated snapshot.
>
> Want me to run a full validation on the changed items?

#### Equivalent flag

```
/cleanmatic:product-spec --status
```

---

### Priority 15 — Record a decision so it's never re-litigated (Decision Register)

**When to use:** You made a deliberate call — kept the old wording, accepted a known trade-off, or resolved a
contradiction — and want it remembered so the skill stops re-raising it. Or you just want to see the decisions
you've recorded.

Every explicit ruling is stored as `DEC-<n>` in `docs/product/decisions.md` (an append-only log). When a new claim
contradicts an *approved* document, the skill surfaces it (Keep / Change / Hybrid) and records your choice here; you
can also record one directly. Once a decision is on file, the skill treats it as settled and won't nag you about the
same drift again — unless the underlying wording actually changes, in which case it asks whether your prior decision
still applies.

#### Conversation

> **You:** Show me the decisions we've locked in.
>
> **Skill:** Recorded decisions:
> - **DEC-1** — Keep guest checkout out of scope for v1 (accepted 2026-05-20).
> - **DEC-2** — Allow the 7-day return window even though a competitor offers 30 (deliberate trade-off).
>
> **You:** Record that we're sticking with email-only login for now.
>
> **Skill:** Logged as **DEC-3** with today's date and your reason. I won't re-raise email-only login as a gap again.

#### Equivalent flag

```
/cleanmatic:product-spec --decision         # list recorded decisions
/cleanmatic:product-spec --decision DEC-2    # view one decision
```

#### Turning a critique into decisions — `--apply-critique`

If you ran **`cleanmatic:product-spec-critique`** (the brutal-but-grounded tear-down) and got a report, this is
how you bring its findings *back into the spec as decisions*. The critique skill only writes a report; it never
touches your spec. `--apply-critique` walks each finding **with you** — **Keep** (reject the finding, record
why), **Change + re-approve** (accept it; the skill runs the impact pass and never rewrites your prose for you),
or **Defer** (revisit later) — and records one `DEC-<n>` per resolved finding so nothing is re-litigated.

It is built to be safe: the report is read only from `docs/product/critique/`, each finding is matched to its
artifact and tagged **fresh / stale / unknown** (so you know if the spec moved since the critique), a *Change*
on an already-approved document goes through the same Keep/Change/Hybrid sign-off gate, and an interrupted run
resumes without double-recording. If a report predates freshness tracking, the skill tells you plainly instead
of guessing.

> **You:** Apply the critique report from this morning.
>
> **Skill:** I read `docs/product/critique/260604-all.md` — 6 findings. Walking them one by one:
> 1. `[blocker] BRD-G2` — the north-star metric. Keep, Change + re-approve, or Defer?
>
> **You:** Change it — add the sustained-conversation metric.
>
> **Skill:** Recorded **DEC-1** (affects BRD-G2). I've flagged the goal for your edit (I won't rewrite the
> wording myself). On to finding 2…

```
/cleanmatic:product-spec --apply-critique docs/product/critique/<report>.md
```

---

### Priority 16 — Make sure nothing important slips through the cracks (the validate "Memory pass")

**When to use:** You don't ask for this — it happens automatically every time you run a quality check (Validate). It's
worth knowing it's there, so you understand why the report ends with a short "what did we remember to write down?" note.

Decisions, corrections, and boundary slips only help later if they're actually *recorded*. So every Validate report ends
with a **Memory pass**: a quick, explicit answer to three questions — did any contradiction become a recorded decision?
did any structural slip get noted so it isn't repeated? are there any "looks unrecorded" signals worth acting on? Even a
plain "nothing to record" is an honest, deliberate answer — not a skipped step. It only ever *prompts* you; it never
records anything behind your back, and it never claims a slip is captured when you've decided it isn't worth recording.

#### Conversation

> **You:** Validate my spec.
>
> **Skill:** Quality report: traceability clean, two quality notes (listed above). And a quick **Memory pass**:
> - 🧠 Decisions: the checkout-scope contradiction we resolved earlier is on file as **DEC-4** — nothing new to add.
> - 🧠 Corrections: no structural slip this round.
> - 🧠 Signals: one note — a file looks like it was edited outside `docs/product/`. Want me to record that as a
>   self-correction, or is it expected?
>
> **You:** It's expected, leave it.
>
> **Skill:** Understood — I'll note it as acknowledged so I don't keep flagging the same thing.

#### Equivalent flag

The Memory pass is built into Validate — there's no separate flag. Just run:

```
/cleanmatic:product-spec --validate
```

---

### Priority 17 — Catch up on memories you skipped earlier (Reflect)

**When to use:** After a long stretch of work — a big import, lots of changes without running Validate, or an old spec you
just brought in — you suspect some decisions or corrections were never written down. Reflect goes back and *harvests* them.

The skill scans what's **written down** — your git history (if any) and the current document/memory state — and proposes
the rulings and corrections that look like they were made but never recorded. Each one is just a **proposal**: you
**accept**, **edit the wording**, or **reject** it, and only the ones you accept get saved. It runs only when you ask
(it spends extra effort to think carefully), and it works even without git — it just harvests from your files. One honest
limit: it can only catch what's *written down*, never something you only *said* in chat.

#### Conversation

> **You:** I imported a big spec and made lots of edits without validating. Can you catch up on anything we should have
> recorded?
>
> **Skill:** I scanned the history and current state. Three things look unrecorded:
> - A commit "revert guest-checkout scope" — looks like a decision. Record as a ruling?
> - A fix "tighten return-window wording" — looks like a self-correction. Note it?
> - Everything else is already on file — nothing to re-propose.
>
> **You:** Yes to the first as a decision, skip the second.
>
> **Skill:** Recorded the scope decision as **DEC-5** with your reason. Left the wording fix alone. Nothing else to catch up.

#### Equivalent flag

```
/cleanmatic:product-spec --reflect
```

---

### Priority 18 — Turn on an automatic memory reminder (opt-in Stop hook)

**When to use:** You (or your build team) want the skill to **remind you at the end of a session** if a decision, a
correction, or a boundary slip looks unrecorded — without having to remember to check yourself. This is an opt-in setup
step, done once.

This reminder is **off by default** and is **never turned on for you automatically** — auto-changing your settings would
be a trust violation. You opt in with one install command, and you can turn it off any time. When on, it gently nudges at
the end of a conversation if something looks unrecorded; only an outside-the-folder boundary breach (an unambiguous slip)
asks you to fix it before finishing.

#### Conversation

> **You:** Can the skill remind me at the end if I forgot to record a decision?
>
> **Skill:** Yes — that's an opt-in reminder, off by default. Run the one-time setup command below to turn it on (it only
> changes your local settings, never anything shared, and you can remove it any time). After that, I'll give you a quick
> end-of-session nudge whenever something looks unrecorded.

#### Equivalent flag

This is an install option, not an in-skill flag. Run once in the project:

```
./install.sh --memory-hook          # turn the reminder on (local settings only)
./install.sh --memory-hook-shared   # turn it on for the whole team (committed settings)
```

A plain `./install.sh` never touches your hooks. To turn it off, remove the `memory_gap_hook.py` entries from your
settings file.

---

### Priority 19 — Tune how hard the skill challenges and suggests (Engagement profile)

**When to use:** The skill probes too hard (or not hard enough), or offers too many next-step suggestions (or too few).
Two knobs let you tune **how the AI engages** — separate from how long the output is (`detail_level`):

- **`interview_rigor`** (`light` / `standard` / `deep`, default `standard`) — how hard the skill **challenges claims
  and hunts for gaps / edge cases / missing acceptance criteria**. Applies at **every** interview level (vision / BRD /
  PRD / epic / story).
- **`action_prompting`** (`minimal` / `standard` / `proactive`, default `standard`) — the **density of next-step
  suggestions** the skill offers each turn.

**These are two independent axes:** `detail_level` = *length* (how much prose); `interview_rigor` = *depth* (how hard
the challenge). **"Concise but deep"** is valid (`detail_level: concise` + `interview_rigor: deep`) — terse output, yet
the skill still pushes back on every unproven claim. Never read `deep` as "write more".

The neutral default is `standard`, so the skill **never silently** puts you in a strict posture — it asks once early
(folded into the `detail_level` question) and writes only on your confirm. At session close, if there's real evidence
(e.g. you kept waving off deep probing as noise), it may propose tightening or relaxing a knob — it writes only if you agree.

#### Equivalent command

```
./.claude/skills/.venv/bin/python3 scripts/preferences.py --root . \
  --set interview_rigor=deep --set action_prompting=proactive
```

This **preserves every other preference** (load→merge→save); a bad value exits non-zero and **writes nothing**.

---

## 4. A typical end-to-end workflow

If you're just starting out, here's the recommended order:

1. **Initialize** the product (vision + personas + core value).
2. **Write the BRD** — lock in business goals and metrics.
3. **Add PRDs** for the most important feature areas.
4. **Split into epics and stories**, with acceptance criteria (or use a "brain-dump" and let the skill
   decompose it).
5. **Validate** to catch structural and quality issues.
6. **Visualize** to see the big picture and spot gaps.
7. **Update** when things change, **approve** when they're mature.
8. **Summarize / export** to share with leadership and other teams.

You don't have to follow this exact order — but it's the smoothest path.

---

## 5. What this skill does NOT do (so you can relax)

- **No code.** This is a product-spec skill. If you need code, the engineering team writes it from the
  stories + acceptance criteria.
- **No story-point or hour estimates.** Stories carry only a `S` / `M` / `L` size.
- **No overwriting your hand-written prose.** On update, the skill flags and asks before regenerating.
- **No auto-reversing an approved decision.** A contradiction is always surfaced for you to choose
  Keep / Change / Hybrid.
- **No internet needed at runtime.** After a one-time install, everything runs on your machine. The
  documents live neatly under `docs/product/` in your project.

---

## 6. Stuck? Just ask the skill directly

The easiest move when stuck: **open the skill and ask in plain words.** For example *"What should I do
next?"* or *"What's missing from my document set?"*. The skill looks at the current state and suggests a
sensible step.

For deeper technical details (for operators), see `SKILL.md` and the `references/` folder in the skill
directory, or the `README.md` at the project root.
