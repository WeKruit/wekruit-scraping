# Research Summary — Milestone v1.1 AI/CS Ranking And Recruiter Readiness

**Researched:** 2026-04-14
**Confidence:** High for milestone direction, medium for a few live source contracts

## Executive Summary

This milestone should not start with scoring code. It should start by constraining the AI/CS
ranking corpus, then normalizing and resolving identities, then enriching key-author and contact
signals, and only then computing explainable ranking outputs.

The biggest correction to the prior generic plan is this: **ranking must be venue-gated before it
is weighted.** Broad concept search is useful for discovery, but it is not a trustworthy ranking
corpus. The milestone therefore needs an explicit `CCF + CORE`-derived AI/CS venue tier asset and a
corpus gate that records why papers are included or excluded.

## Key Findings

### Stack additions

- Local `ai_cs_venue_tiers.csv` asset is mandatory
- OpenAlex author-detail enrichment is mandatory for author influence
- Ranking profiles must be versioned/configured, not hard-coded ad hoc
- Flat Python stages remain the correct implementation shape

### Table-stakes features

- AI/CS corpus gate
- canonical paper/researcher schema
- stable-ID-first identity resolution
- explainable `latest` / `impact` / `balanced` ranking modes
- recruiter-facing CSV/JSONL export with provenance

### Architecture

Recommended order:

1. corpus gate
2. canonical normalization
3. identity graph
4. author-detail + contact-quality enrichment
5. explainable ranking
6. recruiter export

### Watch out for

- concept-search corpus contamination
- stale or conflicting venue tiers
- raw citation counts dominating newer papers
- averaging all coauthors into one “author influence” signal
- black-box score outputs with no breakdown

## Milestone Implications

The milestone should be organized into **five phases** that continue numbering from the current
roadmap:

1. **Phase 6 — AI/CS Corpus Gate And Venue Tiers**
2. **Phase 7 — Canonical Schema And Identity Resolution**
3. **Phase 8 — Author Detail And Contact Quality Enrichment**
4. **Phase 9 — Explainable Ranking Engine**
5. **Phase 10 — Recruiter Export And Calibration**

## Still Needs Live Verification During Implementation

- Exact CCF/CORE mapping asset source and review cadence
- OpenAlex author-detail throughput assumptions at milestone scale
- OpenReview live-access reliability for profile enrichment
