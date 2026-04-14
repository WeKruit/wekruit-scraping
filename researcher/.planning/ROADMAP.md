# Roadmap: Researcher Pipeline

## Overview

This roadmap is milestone-specific for v1.1 AI/CS Ranking And Recruiter Readiness. It replaces the
previous forward-looking phases with the AI/CS-only work needed to close the loop from official
ingest to recruiter-ready ranked outputs. UI/dashboard work and Bio/Pharma expansion remain out of
scope for this milestone.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 6: AI/CS Corpus Gate And Venue Tiers** - Gate the ranking corpus with explicit AI/CS venue-tier rules.
- [ ] **Phase 7: Canonical Schema And Identity Resolution** - Normalize records and merge researchers conservatively.
- [ ] **Phase 8: Author Detail And Contact Quality Enrichment** - Enrich resolved researchers with influence and contact-quality signals.
- [ ] **Phase 9: Explainable Ranking Engine** - Score AI/CS papers and researchers with selectable explainable modes.
- [ ] **Phase 10: Recruiter Export And Calibration** - Review ranked outputs and export recruiter-ready AI/CS datasets.

## Phase Details

### Phase 6: AI/CS Corpus Gate And Venue Tiers
**Goal**: Users can gate the AI/CS ranking corpus through explicit venue-tier rules before any downstream ranking or recruiter export happens.
**Depends on**: Phase 1
**Requirements**: [CORPUS-01, CORPUS-02, CORPUS-03]
**Success Criteria** (what must be TRUE):
  1. User can review a local AI/CS venue-tier table with upstream source, grade, normalized tier, and last-reviewed metadata.
  2. User can run the corpus gate and receive an AI/CS paper set limited to venues that pass explicit inclusion rules.
  3. User can inspect why each paper was included or excluded from the AI/CS ranking corpus.
**Plans**: 3 plans

Plans:
- [ ] 06-01-PLAN.md — Define the AI/CS venue-tier asset and strict source-ID join contract
- [ ] 06-02-PLAN.md — Implement append-only corpus gating over staged OpenAlex works
- [ ] 06-03-PLAN.md — Emit full include/exclude decision logs with lineage-safe rerun semantics

### Phase 7: Canonical Schema And Identity Resolution
**Goal**: Users can work from one canonical AI/CS paper and researcher graph with stable-ID-first identity handling and unresolved ambiguity preserved.
**Depends on**: Phase 6
**Requirements**: [IDENT-01, IDENT-02, IDENT-03]
**Success Criteria** (what must be TRUE):
  1. User can transform staged AI/CS source data into one canonical schema for papers, researchers, venues, affiliations, and contact candidates.
  2. User can see stable identifiers drive cross-source merges before any name-based matching is attempted.
  3. User can keep ambiguous researcher matches unresolved instead of force-merging them.
**Plans**: 3 plans

Plans:
- [ ] 07-01: Define the canonical schema and provenance contract
- [ ] 07-02: Implement normalization from staged source data into canonical records
- [ ] 07-03: Implement stable-ID-first merge rules and unresolved-match handling

### Phase 8: Author Detail And Contact Quality Enrichment
**Goal**: Users can enrich resolved AI/CS researchers with source-native author influence inputs and public contact-quality signals without weakening identity correctness.
**Depends on**: Phase 7
**Requirements**: [ENRICH-01, ENRICH-02, ENRICH-03]
**Success Criteria** (what must be TRUE):
  1. User can backfill key-author details from OpenAlex and inspect the source-native inputs used for author influence.
  2. User can attach AI/CS public profile and homepage signals only to already-resolved researcher identities.
  3. User can inspect each contact candidate with an explicit quality state instead of a binary `has email` flag.
**Plans**: 3 plans

Plans:
- [ ] 08-01: Add OpenAlex author-detail enrichment for influence inputs
- [ ] 08-02: Attach AI/CS profile and homepage signals after identity resolution
- [ ] 08-03: Label contact candidates with quality states and provenance

### Phase 9: Explainable Ranking Engine
**Goal**: Users can rank AI/CS papers and researchers with explainable component scores and selectable scoring modes.
**Depends on**: Phase 8
**Requirements**: [RANK-01, RANK-02, RANK-03]
**Success Criteria** (what must be TRUE):
  1. User can rank AI/CS papers with explicit component scores for recency, citation signal, venue tier, and author influence.
  2. User can rank researcher records from the gated AI/CS corpus and see which paper and influence inputs drove their position.
  3. User can switch between `latest`, `impact`, and `balanced` ranking modes without changing the underlying corpus gate.
  4. User can inspect score breakdowns for each ranked paper and ranked researcher record.
**Plans**: 3 plans

Plans:
- [ ] 09-01: Define versioned ranking profiles and scoring components
- [ ] 09-02: Implement paper and researcher scoring with mode selection
- [ ] 09-03: Emit explainable score breakdown outputs for ranked records

### Phase 10: Recruiter Export And Calibration
**Goal**: Users can manually review ranked AI/CS outputs, then export recruiter-ready papers and researchers with provenance, score context, and contact-quality context retained.
**Depends on**: Phase 9
**Requirements**: [EXPORT-01, EXPORT-02, QUALITY-01]
**Success Criteria** (what must be TRUE):
  1. User can open a calibration output that surfaces top-ranked results and corpus exclusions for manual review before the ranking contract is accepted.
  2. User can export ranked AI/CS papers as CSV and JSONL with provenance and score breakdowns retained.
  3. User can export ranked AI/CS researchers as CSV and JSONL with top-paper context and contact-quality context retained.
**Plans**: 2 plans

Plans:
- [ ] 10-01: Build calibration outputs for top-ranked results and corpus exclusions
- [ ] 10-02: Implement recruiter-facing paper and researcher exports in CSV and JSONL

## Progress

**Execution Order:**
Phases execute in numeric order: 6 → 7 → 8 → 9 → 10

**Historical Note:**
- Phase 1 foundation shipped on 2026-04-13 and is preserved below for continuity.
- Prior forward-looking placeholder Phases 2-5 were replaced by this milestone-specific v1.1 phase set.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Official AI Ingest Foundation | 3/3 | Complete | 2026-04-13 |
| 6. AI/CS Corpus Gate And Venue Tiers | 0/3 | Ready to plan | - |
| 7. Canonical Schema And Identity Resolution | 0/3 | Not started | - |
| 8. Author Detail And Contact Quality Enrichment | 0/3 | Not started | - |
| 9. Explainable Ranking Engine | 0/3 | Not started | - |
| 10. Recruiter Export And Calibration | 0/2 | Not started | - |
