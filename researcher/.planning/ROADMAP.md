# Roadmap: Sourcing Pipeline

## Overview

This roadmap is milestone-specific for v1.2 Sourcing Service And Human Review Foundation. It
reframes the work from a researcher-only merge pipeline into a shared sourcing service across
`wekruit-scraping` and `wekruit-core-service-cloud-function`.

The key architectural decision is:

```text
Python scraping workers -> core-service sourcing ingest API -> Firebase storage/review workflow
```

Python workers keep source execution and local JSONL replay. Core-service owns schema validation,
Firestore/Cloud Storage writes, task orchestration, review labels, and approved entities.

## Phases

**Phase Numbering:**
- Integer phases continue from prior researcher work.
- Phase 1 and Phase 6 are shipped foundations.
- Phase 7-10 from the prior ranking roadmap are superseded until approved entities exist.

- [ ] **Phase 11: Sourcing Firebase Schema And Collection Contract** - Define the core-service sourcing service, zod schemas, Firestore collections, Cloud Storage raw pointer contract, and indexes.
- [ ] **Phase 12: Core Ingest API And Firebase Persistence** - Add source-run and source-record ingest endpoints in core-service and persist validated records to Firebase.
- [ ] **Phase 13: Python Worker Upload Client And Replay Bridge** - Add a Python client in `wekruit-scraping` that uploads local source outputs to the core-service ingest API.
- [ ] **Phase 14: Source Domain Adapter Integration** - Map researcher, Devpost, and GitHub outputs into the generic source-record contract.
- [ ] **Phase 15: Evidence Extraction And Dedup Candidate Generation** - Create auditable evidence records and dedup candidates with explicit evidence-linked reasons.
- [ ] **Phase 16: Human Review And Approved Entity Loop** - Export/query dedup review queues, ingest human labels, suppress repeated reviews, and materialize approved entities.

## Phase Details

### Phase 11: Sourcing Firebase Schema And Collection Contract
**Goal**: Users can review the core-service sourcing contract before any Python worker uploads production data.
**Depends on**: Existing core-service Firebase stack
**Requirements**: [CORE-01, CORE-02, CORE-03, CORE-04, CORE-05, CORE-FOUNDATION-01]
**Success Criteria** (what must be TRUE):
  1. User can see sourcing collection names added beside existing `matching` and `outbound` collections without changing those services.
  2. User can see zod schemas for source runs, source records, evidence records, dedup candidates, review labels, and approved entities.
  3. User can see how large raw payloads are represented through Cloud Storage pointers and content hashes.
  4. User can see all sourcing-owned Firestore collections, Cloud Storage paths, task queues, and HTTP routes use explicit sourcing prefixes.
  5. User can run emulator/typecheck tests proving valid fixtures pass and invalid fixtures fail.
**Plans**: 2 plans

Plans:
- [ ] 11-01: Define sourcing domain schemas and Firestore collection registry
- [ ] 11-02: Add repository fixtures, indexes, and emulator-safe validation tests

### Phase 12: Core Ingest API And Firebase Persistence
**Goal**: Users can send source runs and source records to core-service, where they are validated and persisted to Firebase.
**Depends on**: Phase 11
**Requirements**: [API-01, API-02, API-03, API-04]
**Success Criteria** (what must be TRUE):
  1. User can create a source run through a core-service HTTP endpoint.
  2. User can batch upsert source records through a core-service HTTP endpoint.
  3. User can complete a source run and inspect stored/skipped/failed counts.
  4. Invalid payloads are rejected before Firestore writes.
**Plans**: 2 plans

Plans:
- [ ] 12-01: Implement source-run and source-record ingest application services
- [ ] 12-02: Expose sourcing HTTP API and verify Firebase persistence in emulator tests

### Phase 13: Python Worker Upload Client And Replay Bridge
**Goal**: Users can keep running Python scraping locally while uploading schema-valid source records to core-service.
**Depends on**: Phase 12
**Requirements**: [PY-01, PY-02, PY-03]
**Success Criteria** (what must be TRUE):
  1. User can upload a local JSONL replay run to the core-service ingest API.
  2. User can run a Python worker and have it create/complete a source run through core-service.
  3. User can keep local JSONL artifacts for replay/debug without treating local files as product storage.
**Plans**: 2 plans

Plans:
- [ ] 13-01: Add Python sourcing ingest client and local schema preflight
- [ ] 13-02: Add JSONL replay uploader and end-to-end local ingest POC

### Phase 14: Source Domain Adapter Integration
**Goal**: Users can map existing scraping outputs into the generic source-record contract, with researcher as the first merge-heavy domain.
**Depends on**: Phase 13
**Requirements**: [DOMAIN-01, DOMAIN-02, DOMAIN-03, DOMAIN-04, DOMAIN-05]
**Success Criteria** (what must be TRUE):
  1. User can upload researcher OpenAlex records as `domain=researcher` source records.
  2. User can upload researcher ORCID, DBLP, and OpenReview records as `domain=researcher` source records.
  3. User can upload Devpost and GitHub records through the same generic source-record contract.
  4. Adding a new source only requires a source adapter and does not require a new Firestore collection.
**Plans**: 3 plans

Plans:
- [ ] 14-01: Map researcher OpenAlex/ORCID/DBLP/OpenReview outputs to source records
- [ ] 14-02: Map Devpost outputs to source records
- [ ] 14-03: Map GitHub outputs to source records and document new-source adapter rules

### Phase 15: Evidence Extraction And Dedup Candidate Generation
**Goal**: Users can see auditable evidence for why source records may represent the same entity without approving the merge automatically.
**Depends on**: Phase 14
**Requirements**: [EVIDENCE-01, EVIDENCE-02, EVIDENCE-03, DEDUP-01, DEDUP-02, DEDUP-03, DEDUP-04]
**Success Criteria** (what must be TRUE):
  1. User can create evidence records with source provenance, normalized value, value hash, quality state, and extractor version.
  2. User can create dedup candidates from exact and review-worthy evidence.
  3. User can inspect machine-readable reasons, referenced evidence IDs, and suggested strength for each dedup candidate.
  4. No approved entity is created by dedup candidate strength alone.
**Plans**: 3 plans

Plans:
- [ ] 15-01: Implement evidence extraction over stored source records
- [ ] 15-02: Implement dedup candidate generation from evidence
- [ ] 15-03: Emit dedup reasoning packets with evidence links and strength labels

### Phase 16: Human Review And Approved Entity Loop
**Goal**: Users can review dedup candidates manually and produce approved entities only after human labels.
**Depends on**: Phase 15
**Requirements**: [REVIEW-01, REVIEW-02, REVIEW-03, APPROVE-01, APPROVE-02]
**Success Criteria** (what must be TRUE):
  1. User can export or query reviewer-ready dedup candidate queues.
  2. User can ingest `same_person`, `not_same_person`, and `unsure` labels.
  3. Negative and unsure labels suppress repeated review spam unless materially new evidence appears.
  4. Only `same_person` labels can materialize approved entities.
  5. User can export approved entities separately from unresolved dedup candidates.
**Plans**: 3 plans

Plans:
- [ ] 16-01: Add review queue API/export
- [ ] 16-02: Add label ingest and repeated-candidate suppression
- [ ] 16-03: Materialize and export approved entities

## Progress

**Execution Order:**
Phases execute in numeric order: 11 → 12 → 13 → 14 → 15 → 16

**Historical Note:**
- Phase 1 official-source researcher ingest foundation shipped on 2026-04-13.
- Phase 6 AI/CS corpus gate shipped on 2026-04-14.
- The prior researcher-only v1.2 Postgres direction is superseded by this Firebase/core-service sourcing plan.
- Outbound integration is the next consumer after approved entities exist; unresolved dedup candidates must not be written to `outbound-candidates`.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Official AI Ingest Foundation | 3/3 | Complete | 2026-04-13 |
| 6. AI/CS Corpus Gate And Venue Tiers | 3/3 | Complete | 2026-04-14 |
| 11. Sourcing Firebase Schema And Collection Contract | 0/2 | Ready to plan | - |
| 12. Core Ingest API And Firebase Persistence | 0/2 | Not started | - |
| 13. Python Worker Upload Client And Replay Bridge | 0/2 | Not started | - |
| 14. Source Domain Adapter Integration | 0/3 | Not started | - |
| 15. Evidence Extraction And Dedup Candidate Generation | 0/3 | Not started | - |
| 16. Human Review And Approved Entity Loop | 0/3 | Not started | - |
