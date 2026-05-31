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

#### Equivalent flag

```
/cleanmatic:product-spec                # no flag → skill sees nothing exists → offers to initialize
/cleanmatic:product-spec --product      # go straight to creating/refreshing PRODUCT.md
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
criteria, duplicate IDs), and a judgment layer (story quality, vagueness, value drift, semantic duplication).
The result is an **easy-to-read report**.

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

#### Equivalent flag

```
/cleanmatic:product-spec --summary
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
```

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
