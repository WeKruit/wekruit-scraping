# Feature Research — Milestone v1.1 AI/CS Ranking And Recruiter Readiness

**Scope:** Feature set for the current milestone only.
**Researched:** 2026-04-14
**Confidence:** High

## Category 1 — Corpus Gate

**Table stakes**
- Explicit AI/CS corpus gate before ranking
- Venue-tier-backed inclusion rules
- Clear `excluded_reason` for papers filtered out

**Differentiators**
- Hybrid `CCF + CORE` mapping with normalized internal tiers
- Ability to explain why a paper was included even if concept search was broad

**Anti-features**
- Ranking directly off OpenAlex concept search output
- Mixing Bio/Pharma papers into the same ranked set
- Treating unknown venues as equal to top-tier venues

## Category 2 — Canonical Identity

**Table stakes**
- Canonical paper schema
- Canonical researcher schema
- Stable-ID-first identity merge
- Ambiguity state instead of force-merge

**Differentiators**
- Paper-to-key-author linkage preserved for author-influence scoring
- Field-level provenance on normalized facts used in ranking/export

**Anti-features**
- Name-first matching
- Ranking directly off raw staged source records

## Category 3 — Influence And Contact Signals

**Table stakes**
- OpenAlex author-detail enrichment for key-author metrics
- Public profile/contact provenance retained
- Contact quality state retained instead of binary `has_email`

**Differentiators**
- Separate “research influence” from “contact actionability”
- Distinguish homepage-derived signals from direct public profile signals

**Anti-features**
- Letting contact availability distort identity logic
- Treating any scraped email as equal-confidence recruiter output

## Category 4 — Explainable Ranking

**Table stakes**
- Paper ranking by `time / citation / venue / author influence`
- Multiple ranking modes: `latest`, `impact`, `balanced`
- Per-record score breakdown available in output

**Differentiators**
- Year-normalized citation signal instead of raw total citations only
- Recruiter-friendly explanation of why something ranked highly

**Anti-features**
- Single opaque score with no component breakdown
- Prestige-only ranking objective
- Mixing recency and citation without normalization

## Category 5 — Recruiter Export

**Table stakes**
- Ranked paper export
- Ranked researcher export
- CSV + JSONL output
- Provenance columns retained

**Differentiators**
- Export includes component scores, top venue, last publication date, and contact quality summary
- Export schema stable enough for downstream sourcing flows

**Anti-features**
- “Pretty” exports without traceability
- Exporting unresolved ambiguous identities as if they were final

## What Belongs In This Milestone

1. Close the AI/CS-only paper-to-researcher-to-rank loop.
2. Make ranking auditable by humans.
3. Produce recruiter-usable outputs from that ranked set.

## What Stays Out

1. Bio/Pharma ranking or mixed-domain ranking.
2. Dashboard/UI work.
3. Commercial enrichment waterfall as a primary dependency.
4. Generic search expansion beyond the venue-gated AI/CS corpus.
