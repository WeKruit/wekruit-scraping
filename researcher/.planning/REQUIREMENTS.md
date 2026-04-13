# Requirements: Researcher Pipeline

**Defined:** 2026-04-13
**Core Value:** Produce high-confidence researcher profiles with defensible provenance so downstream sourcing and outreach can trust who the researcher is, what they worked on, and how the contact signal was found.

## v1 Requirements

### Ingest

- [ ] **INGEST-01**: User can run official-source paper and author ingest without relying on generic web crawling.
- [ ] **INGEST-02**: User can target AI/ML papers through concept, venue, or keyword presets.
- [ ] **INGEST-03**: User can replay raw source-native paper and author staging files for the same run configuration.

### Identity

- [ ] **IDENT-01**: User can normalize papers, researchers, affiliations, and contacts into one canonical schema.
- [ ] **IDENT-02**: User can merge researcher identities using stable identifiers before any name-based matching.

### Enrichment

- [ ] **ENRICH-01**: User can enrich merged researcher profiles with ORCID identity and employment data through a credentialed, compliance-aware path.
- [ ] **ENRICH-02**: User can enrich AI/CS profiles with OpenReview and DBLP signals without treating those sources as direct email databases.
- [ ] **ENRICH-03**: User can attach secondary public contact hints from homepages or PubMed/PMC with explicit provenance.

### Quality

- [ ] **QUALITY-01**: User can see quality state for each contact candidate instead of a binary “has email” flag.
- [ ] **QUALITY-02**: User can rerun the pipeline incrementally with per-source limits, retries, and audit metadata preserved.

### Export

- [ ] **EXPORT-01**: User can rank researchers using topical fit, recency, publication/citation signal, and contact quality.
- [ ] **EXPORT-02**: User can export ranked researcher profiles as CSV and JSONL with source provenance retained.

### Expansion

- [ ] **EXPAND-01**: User can add at least one non-AI source family to the same schema after the AI/ML loop works.
- [ ] **EXPAND-02**: User can expand domain presets without redesigning the canonical profile shape.

## v2 Requirements

### Commercial Waterfall

- **WATER-01**: User can plug verified third-party enrichment tools into the contact pipeline after the core profile quality is proven.

### Coverage Expansion

- **COVER-01**: User can support additional scholarly source families such as Europe PMC, ACL Anthology, or arXiv once the first expansion path is stable.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Generic crawl-first discovery | Conflicts with the official-source backbone and increases schema/compliance risk |
| Dashboard or operator UI | Not needed before the data pipeline is correct |
| Closed-platform or login-gated scraping | Outside the source policy for this project |
| Guaranteed direct-email coverage | Contact is an enrichment output with varying quality and legality constraints |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INGEST-01 | Phase 1 | Pending |
| INGEST-02 | Phase 1 | Pending |
| INGEST-03 | Phase 1 | Pending |
| IDENT-01 | Phase 2 | Pending |
| IDENT-02 | Phase 2 | Pending |
| ENRICH-01 | Phase 3 | Pending |
| ENRICH-02 | Phase 3 | Pending |
| ENRICH-03 | Phase 3 | Pending |
| QUALITY-01 | Phase 3 | Pending |
| QUALITY-02 | Phase 1 | Pending |
| EXPORT-01 | Phase 4 | Pending |
| EXPORT-02 | Phase 4 | Pending |
| EXPAND-01 | Phase 5 | Pending |
| EXPAND-02 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-13*
*Last updated: 2026-04-13 after initial definition*
