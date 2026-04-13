# Roadmap: Researcher Pipeline

## Overview

This roadmap moves from deterministic AI/ML ingest to identity correctness, then contact
enrichment, recruiter-facing ranking/export, and only then broader domain expansion. The ordering
is driven by correctness: source truth first, merge correctness second, contact quality third.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Official AI Ingest Foundation** - Build the AI/ML-first official-source ingest and raw staging backbone.
- [ ] **Phase 2: Canonical Schema And Identity Graph** - Normalize records and merge researchers conservatively.
- [ ] **Phase 3: Contact Enrichment And Quality** - Attach public contact signals with provenance and quality labels.
- [ ] **Phase 4: Ranking And Recruiter Export** - Score profiles for recruiting use and export ranked outputs.
- [ ] **Phase 5: Domain Expansion And Source Hardening** - Add the first non-AI expansion path without changing the core schema.

## Phase Details

### Phase 1: Official AI Ingest Foundation
**Goal**: Deliver a replayable AI/ML ingest path from official scholarly sources with raw staging and source-aware run metadata.
**Depends on**: Nothing (first phase)
**Requirements**: [INGEST-01, INGEST-02, INGEST-03, QUALITY-02]
**Success Criteria** (what must be TRUE):
  1. User can run the pipeline for an AI/ML venue, concept, or keyword slice and receive raw paper/author outputs from official scholarly sources.
  2. Raw outputs preserve source-native fields plus run metadata needed for replay and audit.
  3. Source limits, retries, and incremental reruns work without changing record semantics.
**Plans**: 3 plans

Plans:
- [ ] 01-01: Define config, source registry, run metadata, and raw staging contract
- [ ] 01-02: Implement OpenAlex-led ingest and AI/ML query presets
- [ ] 01-03: Add Crossref metadata backfill and replay/incremental controls

### Phase 2: Canonical Schema And Identity Graph
**Goal**: Deliver one canonical researcher model with stable-ID-first merge rules and ambiguity-aware identity handling.
**Depends on**: Phase 1
**Requirements**: [IDENT-01, IDENT-02]
**Success Criteria** (what must be TRUE):
  1. User can transform source-native staged data into one canonical profile shape for papers, researchers, affiliations, and contacts.
  2. Stable IDs are used before names when linking records across sources.
  3. Ambiguous matches remain unresolved instead of being force-merged.
**Plans**: 3 plans

Plans:
- [ ] 02-01: Define canonical profile schema and field-level provenance model
- [ ] 02-02: Implement normalization transforms from staged source data
- [ ] 02-03: Implement conservative merge rules and ambiguity handling

### Phase 3: Contact Enrichment And Quality
**Goal**: Deliver a compliance-aware contact enrichment layer that attaches public signals only after identity is stable.
**Depends on**: Phase 2
**Requirements**: [ENRICH-01, ENRICH-02, ENRICH-03, QUALITY-01]
**Success Criteria** (what must be TRUE):
  1. User can enrich merged researcher profiles with ORCID and AI/CS profile signals through explicit source contracts.
  2. Contact candidates retain source provenance and quality state.
  3. Homepage or PubMed/PMC contact hints are attached only to already-merged profiles.
**Plans**: 3 plans

Plans:
- [ ] 03-01: Validate ORCID source contract and implement compliance-aware identity enrichment
- [ ] 03-02: Add OpenReview and DBLP profile enrichment for AI/CS researchers
- [ ] 03-03: Add secondary homepage/PubMed contact enrichment and quality labeling

### Phase 4: Ranking And Recruiter Export
**Goal**: Deliver recruiter-facing ranked outputs that reflect relevance and actionability, not only academic prestige.
**Depends on**: Phase 3
**Requirements**: [EXPORT-01, EXPORT-02]
**Success Criteria** (what must be TRUE):
  1. User can produce a ranked researcher list that incorporates topic fit, recency, research signal, and contact quality.
  2. User can export ranked profiles in CSV and JSONL with provenance retained.
  3. Ranking logic remains explainable enough to audit why a profile was prioritized.
**Plans**: 2 plans

Plans:
- [ ] 04-01: Implement recruiter-oriented scoring inputs and weighting
- [ ] 04-02: Implement ranked CSV/JSONL export and output validation

### Phase 5: Domain Expansion And Source Hardening
**Goal**: Deliver the first broader-domain expansion on the same schema and harden source contracts discovered in earlier phases.
**Depends on**: Phase 4
**Requirements**: [EXPAND-01, EXPAND-02]
**Success Criteria** (what must be TRUE):
  1. User can add at least one non-AI source family or domain preset without redesigning the core profile model.
  2. Source-specific contracts and operational controls are documented and hardened based on earlier phase learnings.
  3. The expanded path still produces the same canonical export shape.
**Plans**: 2 plans

Plans:
- [ ] 05-01: Select first non-AI expansion path and map it onto the canonical schema
- [ ] 05-02: Harden source contracts, limits, and operational runbook for expanded coverage

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Official AI Ingest Foundation | 0/3 | Not started | - |
| 2. Canonical Schema And Identity Graph | 0/3 | Not started | - |
| 3. Contact Enrichment And Quality | 0/3 | Not started | - |
| 4. Ranking And Recruiter Export | 0/2 | Not started | - |
| 5. Domain Expansion And Source Hardening | 0/2 | Not started | - |
