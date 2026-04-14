# Requirements: Researcher Pipeline

**Defined:** 2026-04-14
**Milestone:** v1.1 AI/CS Ranking And Recruiter Readiness
**Core Value:** Produce high-confidence researcher profiles with defensible provenance so downstream sourcing and outreach can trust who the researcher is, what they worked on, and how the contact signal was found.

## Foundation Requirements (Validated)

- [x] **INGEST-01**: User can run official-source paper and author ingest without relying on generic web crawling.
- [x] **INGEST-02**: User can target AI/ML papers through concept, venue, or keyword presets.
- [x] **INGEST-03**: User can replay raw source-native paper and author staging files for the same run configuration.
- [x] **QUALITY-02**: User can rerun the ingest pipeline incrementally with per-source limits, retries, and audit metadata preserved.

## Milestone v1.1 Requirements

### Corpus Gate

- [ ] **CORPUS-01**: User can restrict the AI/CS ranking corpus to papers that pass explicit venue-tier inclusion rules.
- [ ] **CORPUS-02**: User can review a local AI/CS venue-tier table that preserves upstream source, grade, normalized tier, and last-reviewed metadata.
- [ ] **CORPUS-03**: User can see why a paper was included or excluded from the AI/CS ranking corpus.

### Identity Graph

- [ ] **IDENT-01**: User can normalize AI/CS papers, researchers, venues, affiliations, and contact candidates into one canonical schema.
- [ ] **IDENT-02**: User can merge researcher identities using stable identifiers before any name-based matching.
- [ ] **IDENT-03**: User can keep ambiguous researcher matches unresolved instead of force-merging them.

### Influence And Contact Enrichment

- [ ] **ENRICH-01**: User can backfill key-author details from OpenAlex so author influence is computed from explicit source-native metrics.
- [ ] **ENRICH-02**: User can attach public AI/CS profile and homepage signals only after researcher identity is resolved.
- [ ] **ENRICH-03**: User can see a quality state for each contact candidate instead of a binary `has email` flag.

### Explainable Ranking

- [ ] **RANK-01**: User can rank AI/CS papers with explicit component scores for recency, citation signal, venue tier, and author influence.
- [ ] **RANK-02**: User can choose between `latest`, `impact`, and `balanced` ranking modes.
- [ ] **RANK-03**: User can inspect score breakdowns for each ranked paper and ranked researcher record.

### Recruiter Export

- [ ] **EXPORT-01**: User can export ranked AI/CS papers as CSV and JSONL with provenance and score breakdown retained.
- [ ] **EXPORT-02**: User can export ranked AI/CS researchers as CSV and JSONL with top-paper context and contact-quality context retained.

### Calibration And Review

- [ ] **QUALITY-01**: User can run a calibration view that surfaces top-ranked outputs and corpus exclusions for manual review before the ranking contract is accepted.

## Future Requirements

- [ ] **WATER-01**: User can plug verified third-party enrichment tools into the contact pipeline after the AI/CS profile quality is proven.
- [ ] **BIO-01**: User can support a Bio/Pharma ranking track without sharing venue or citation semantics with the AI/CS track.
- [ ] **EXPAND-01**: User can add at least one non-AI source family to the same canonical schema after the AI/CS loop works.
- [ ] **EXPAND-02**: User can expand domain presets without redesigning the canonical profile shape.
- [ ] **COVER-01**: User can support additional scholarly source families such as Europe PMC, ACL Anthology, or arXiv once the first expansion path is stable.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Ranking directly from broad concept search output | Corpus quality is not trustworthy enough for ranking decisions |
| Mixing Bio/Pharma into the AI/CS ranking track | Venue and citation semantics differ too much for the first ranking milestone |
| Generic crawl-first discovery | Conflicts with the official-source backbone and increases schema/compliance risk |
| Dashboard or operator UI | Not needed before the ranking/export contract is correct |
| Closed-platform or login-gated scraping | Outside the source policy for this project |
| Guaranteed direct-email coverage | Contact is an enrichment output with varying quality and legality constraints |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INGEST-01 | Phase 1 | Validated |
| INGEST-02 | Phase 1 | Validated |
| INGEST-03 | Phase 1 | Validated |
| QUALITY-02 | Phase 1 | Validated |
| CORPUS-01 | Unmapped | Pending |
| CORPUS-02 | Unmapped | Pending |
| CORPUS-03 | Unmapped | Pending |
| IDENT-01 | Unmapped | Pending |
| IDENT-02 | Unmapped | Pending |
| IDENT-03 | Unmapped | Pending |
| ENRICH-01 | Unmapped | Pending |
| ENRICH-02 | Unmapped | Pending |
| ENRICH-03 | Unmapped | Pending |
| RANK-01 | Unmapped | Pending |
| RANK-02 | Unmapped | Pending |
| RANK-03 | Unmapped | Pending |
| EXPORT-01 | Unmapped | Pending |
| EXPORT-02 | Unmapped | Pending |
| QUALITY-01 | Unmapped | Pending |

**Coverage:**
- Foundation requirements validated: 4
- Milestone v1.1 requirements: 12
- Future requirements deferred: 5

---
*Last updated: 2026-04-14 after milestone v1.1 requirement scoping*
