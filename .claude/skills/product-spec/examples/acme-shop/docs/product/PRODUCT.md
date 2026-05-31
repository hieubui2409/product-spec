---
id: PRODUCT
type: product
status: approved
lang: en
owner: Jane Doe
version: 1.4.0
created: 2024-06-01
updated: 2026-05-20
name: "Acme Shop"
one_line_description: "A direct-to-fan storefront for boutique fashion brands."
current_implementation: "Live in production ~2 years; 120+ brands onboarded, checkout/catalog/payouts shipped."
deployment: "Multi-region Vercel edge + Supabase Postgres (read replicas in US/EU); Stripe Connect for payouts."
roadmap_one_liner: "Year 2: ship fan-CRM (the differentiator) plus brand analytics; native mobile and cross-brand discovery planned next."
core_value: "Help boutique brands sell directly to their fans and keep a fan relationship that marketplaces never give them."
personas: [shopper, brand-owner, store-admin, ops-manager, support-agent]
---

# Acme Shop — Product Context

> Thin labels only. Narrative lives in `vision.md`. Stakeholders / business goals live in `brd.md`.

## One-Line Description

A direct-to-fan storefront for boutique fashion brands.

## Core Value

_(authoritative value lives in frontmatter `core_value` field — see top of file. Body deliberately blank to keep one source of truth.)_

## Current Implementation

Live in production ~2 years. Launched June 2024 with the core storefront (catalog, checkout, payouts). 120+ boutique
brands onboarded; ~$2.4M cumulative GMV. Year 2 is shipping the fan-CRM differentiator and a brand analytics dashboard.

## Deployment

Multi-region Vercel edge + Supabase Postgres (read replicas in US/EU). Payments and brand payouts run on Stripe Connect.

## Roadmap One-Liner

Year 2: ship fan-CRM (the differentiator) plus brand analytics; native mobile and cross-brand discovery planned next.

## Personas

- shopper — returning fan of a small brand; values direct connection and pays a premium.
- brand-owner — owns/runs one boutique brand; the decision-maker; wants a low-overhead storefront and to keep most of the revenue.
- store-admin — a brand's day-to-day staff; manages catalog, inventory, and orders.
- ops-manager — Acme internal; owns brand onboarding and payout operations.
- support-agent — Acme internal; handles shopper and brand support tickets.
