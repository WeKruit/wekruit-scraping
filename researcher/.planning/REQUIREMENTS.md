# Requirements: Sourcing Pipeline

**Defined:** 2026-04-15
**Milestone:** v1.2 Sourcing Service And Human Review Foundation
**Core Value:** Turn heterogeneous scraping outputs into durable, reviewable, source-backed entities with explicit reasoning, without forcing all source-specific payloads into SQL columns or rewriting working Python scrapers into TypeScript.

## Foundation Requirements (Validated)

- [x] **INGEST-01**: User can run official-source researcher paper and author ingest without relying on generic web crawling.
- [x] **INGEST-02**: User can target AI/ML papers through concept, venue, or keyword presets.
- [x] **INGEST-03**: User can replay raw source-native paper and author staging files for the same run configuration.
- [x] **QUALITY-02**: User can rerun the ingest pipeline incrementally with per-source limits, retries, and audit metadata preserved.
- [x] **CORPUS-01**: User can restrict the AI/CS ranking corpus to papers that pass explicit venue-tier inclusion rules.
- [x] **CORPUS-02**: User can review a local AI/CS venue-tier table that preserves upstream source, grade, normalized tier, and last-reviewed metadata.
- [x] **CORPUS-03**: User can see why a paper was included or excluded from the AI/CS ranking corpus.
- [x] **CORE-FOUNDATION-01**: Core-service already provides Firebase Functions, Firestore, zod, repository patterns, task queues, emulator config, and centralized collection naming.

## Milestone v1.2 Requirements

### Core-Service Sourcing Contract

- [ ] **CORE-01**: User can review a `sourcing` service plan that follows the existing core-service file-management pattern: `domain`, `application`, `repositories`, `functions/http`, and `functions/tasks`.
- [ ] **CORE-02**: User can validate source runs, source records, evidence records, dedup candidates, review labels, and approved entities through zod schemas before Firestore writes.
- [ ] **CORE-03**: User can store large raw payloads through Cloud Storage pointers while Firestore stores queryable summaries, IDs, hashes, and review state.
- [ ] **CORE-04**: User can query sourcing Firestore collections without disrupting existing `matching` and `outbound` services.
- [ ] **CORE-05**: User can verify every sourcing-owned Firestore collection, Cloud Storage raw path, Cloud Tasks queue, and HTTP route uses explicit sourcing prefixes: `sourcing-*`, `sourcing/raw/...`, `sourcing-*`, and `/api/sourcing/...`.

### Core-Service Ingest API

- [ ] **API-01**: User can create a source run through a core-service HTTP endpoint.
- [ ] **API-02**: User can batch upsert source records through a core-service HTTP endpoint.
- [ ] **API-03**: User can complete a source run and inspect received, stored, skipped, failed, and content-hash duplicate counts.
- [ ] **API-04**: User can reject invalid source-record payloads before they reach Firestore.

### Python Worker Integration

- [ ] **PY-01**: User can run Python scraping workers locally and upload records through the core-service API instead of writing directly to Firebase.
- [ ] **PY-02**: User can preserve local JSONL run artifacts for replay/debug while treating core-service/Firebase as product storage.
- [ ] **PY-03**: User can upload a previous local JSONL run to core-service as a replay without re-fetching the source.

### Source Domain Integration

- [ ] **DOMAIN-01**: User can map researcher OpenAlex outputs into generic `domain=researcher` source records.
- [ ] **DOMAIN-02**: User can map researcher ORCID, DBLP, and OpenReview outputs into generic `domain=researcher` source records.
- [ ] **DOMAIN-03**: User can map existing `devpost` outputs into generic source records.
- [ ] **DOMAIN-04**: User can map existing `github` outputs into generic source records.
- [ ] **DOMAIN-05**: User can add a future source by implementing the source-record contract without changing core Firestore collections.

### Evidence Extraction And Dedup Candidate Generation

- [ ] **EVIDENCE-01**: User can create first-class evidence records from source records for email, ORCID, GitHub, homepage, DBLP PID, OpenReview ID, Google Scholar ID, institution, paper DOI, source-native IDs, and source URLs.
- [ ] **EVIDENCE-02**: User can inspect each evidence record with `sourceRecordId`, `evidenceType`, `rawValue`, `normalizedValue`, `valueHash`, extraction path, source URL, quality state, observed timestamp, and extractor version.
- [ ] **EVIDENCE-03**: User can inspect evidence provenance and quality before the evidence participates in dedup candidate generation.
- [ ] **DEDUP-01**: User can generate dedup candidates from exact and review-worthy evidence without automatically merging entities.
- [ ] **DEDUP-02**: User can see machine-readable reasons for every dedup candidate, such as `orcid_exact`, `email_exact`, `github_exact`, `homepage_exact`, `dblp_link`, `paper_overlap`, or `name_institution`.
- [ ] **DEDUP-03**: User can verify every dedup reason points to one or more evidence IDs instead of free-text-only reasoning.
- [ ] **DEDUP-04**: User can see suggested strength (`strong`, `medium`, `weak`) without that strength becoming an approval decision.

### Human Review And Approved Entities

- [ ] **REVIEW-01**: User can export or query a human review queue with dedup candidate ID, source records, names, institutions, evidence, reasons, suggested strength, `human_label`, and notes.
- [ ] **REVIEW-02**: User can ingest human labels: `same_person`, `not_same_person`, and `unsure`.
- [ ] **REVIEW-03**: User can preserve negative and unsure labels so repeated pipeline runs do not keep re-surfacing the same already-reviewed candidates.
- [ ] **APPROVE-01**: User can create approved entities only from human-labeled `same_person` dedup candidates.
- [ ] **APPROVE-02**: User can export approved entities separately from unresolved dedup candidates.

## Future Requirements

- [ ] **CLOUDRUN-01**: User can run Python scraping workers as Cloud Run Jobs after the local-worker ingest contract is proven.
- [ ] **UI-01**: User can review dedup candidates in a dedicated reviewer UI after the API/CSV/JSONL workflow is stable.
- [ ] **RANK-01**: User can rank AI/CS papers with explicit component scores for recency, citation signal, venue tier, and author influence.
- [ ] **RANK-02**: User can choose between `latest`, `impact`, and `balanced` ranking modes.
- [ ] **EXPORT-01**: User can export ranked AI/CS researchers with top-paper context and contact-quality context retained.
- [ ] **GRAPH-01**: User can project approved entities into Neo4j or another graph read model if traversal becomes a measured product need.
- [ ] **OUTBOUND-01**: User can convert a human-approved entity into an `outbound-candidates` record only after approved contact evidence satisfies the current outbound-required fields.
- [ ] **OUTBOUND-02**: User can trace an outbound candidate back to the approved entity, review label, dedup candidate, evidence records, and source records that produced it.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Rewriting Python scrapers into TypeScript | Adds migration risk without improving sourcing correctness |
| Python workers writing directly to Firestore | Bypasses core-service schema, auth, logging, and product write ownership |
| Postgres as v1.2 primary store | Conflicts with schema-document preference and existing Firebase backend |
| MongoDB or another new document DB | Firebase already exists in core-service |
| Neo4j as primary store | Current bottleneck is evidence and human review, not graph traversal |
| Automatic person/entity merge | User explicitly wants every candidate reviewed by a human |
| Full reviewer UI | API/CSV/JSONL review loop is enough before UI investment |
| Ranking from unreviewed identities | Ranking before approved entities would amplify uncertain merge state |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INGEST-01 | Phase 1 | Validated |
| INGEST-02 | Phase 1 | Validated |
| INGEST-03 | Phase 1 | Validated |
| QUALITY-02 | Phase 1 | Validated |
| CORPUS-01 | Phase 6 | Validated |
| CORPUS-02 | Phase 6 | Validated |
| CORPUS-03 | Phase 6 | Validated |
| CORE-FOUNDATION-01 | Phase 11 | Validated |
| CORE-01 | Phase 11 | Pending |
| CORE-02 | Phase 11 | Pending |
| CORE-03 | Phase 11 | Pending |
| CORE-04 | Phase 11 | Pending |
| CORE-05 | Phase 11 | Pending |
| API-01 | Phase 12 | Pending |
| API-02 | Phase 12 | Pending |
| API-03 | Phase 12 | Pending |
| API-04 | Phase 12 | Pending |
| PY-01 | Phase 13 | Pending |
| PY-02 | Phase 13 | Pending |
| PY-03 | Phase 13 | Pending |
| DOMAIN-01 | Phase 14 | Pending |
| DOMAIN-02 | Phase 14 | Pending |
| DOMAIN-03 | Phase 14 | Pending |
| DOMAIN-04 | Phase 14 | Pending |
| DOMAIN-05 | Phase 14 | Pending |
| EVIDENCE-01 | Phase 15 | Pending |
| EVIDENCE-02 | Phase 15 | Pending |
| EVIDENCE-03 | Phase 15 | Pending |
| DEDUP-01 | Phase 15 | Pending |
| DEDUP-02 | Phase 15 | Pending |
| DEDUP-03 | Phase 15 | Pending |
| DEDUP-04 | Phase 15 | Pending |
| REVIEW-01 | Phase 16 | Pending |
| REVIEW-02 | Phase 16 | Pending |
| REVIEW-03 | Phase 16 | Pending |
| APPROVE-01 | Phase 16 | Pending |
| APPROVE-02 | Phase 16 | Pending |

**Coverage:**
- Foundation requirements validated: 8
- Milestone v1.2 requirements: 29
- Future requirements deferred: 8

---
*Last updated: 2026-04-15 after milestone v1.2 sourcing-service phase plan*
