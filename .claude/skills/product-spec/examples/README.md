# Examples — Worked Sample Spec

This directory ships a small, end-to-end product spec built with the skill so you can see the file layout, frontmatter conventions, and ID grammar in practice.

## acme-shop/

A tiny direct-to-fan storefront product, taken through the full hierarchy:

- `docs/product/PRODUCT.md` — thin labels (name, one-liner, core-value, personas).
- `docs/product/vision.md` — narrative vision + personas + north-star.
- `docs/product/brd.md` — BRD with two goals (`BRD-G1`, `BRD-G2`).
- `docs/product/prds/checkout.md` — one PRD (`PRD-CHECKOUT`) covering the checkout flow.
- `docs/product/epics/PRD-CHECKOUT-E1.md` — sign-in + checkout epic.
- `docs/product/stories/PRD-CHECKOUT-E1-S1.md` — magic-link sign-in story with two AC.
- `docs/product/visuals/tree.md` — rendered Mermaid traceability tree.

## Verify it Validates

From the repo root:

```bash
python3 .claude/skills/product-spec/scripts/check_traceability.py \
  --root .claude/skills/product-spec/examples/acme-shop

python3 .claude/skills/product-spec/scripts/check_consistency.py \
  --root .claude/skills/product-spec/examples/acme-shop
```

Both should report zero findings.

## Render the Tree

```bash
python3 .claude/skills/product-spec/scripts/visualize.py \
  --root .claude/skills/product-spec/examples/acme-shop \
  --view tree --format ascii
```

Self-contained HTML renders (any of the 9 views) regenerate on demand:

```bash
python3 .claude/skills/product-spec/scripts/visualize.py \
  --root .claude/skills/product-spec/examples/acme-shop \
  --view tree --format html
```

Each render lands at `docs/product/visuals/<view>-<timestamp>.html`. They are
deliberately not committed (each Mermaid-format render embeds the vendored
Mermaid runtime → ~2.5 MB per file). The single committed `visuals/tree.md`
is the lightweight Mermaid-in-markdown reference.

## What's Intentionally Not Shown

This worked example is intentionally lean (one PRD, one epic, one story). Real spec trees grow larger; the same conventions apply. The `examples/` directory is a reference shape, not a starter template — for that, invoke the skill on your own product.
