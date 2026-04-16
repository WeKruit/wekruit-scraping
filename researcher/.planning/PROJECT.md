# Sourcing Pipeline

## What This Is

This project defines the shared WeKruit sourcing pipeline across `wekruit-scraping` and
`wekruit-core-service-cloud-function`.

`wekruit-scraping` remains the Python execution layer for fetching, scraping, parsing, local JSONL
replay, and source-specific normalization. `wekruit-core-service-cloud-function` becomes the
schema-first ingestion and review backend using the existing Firebase/Cloud Functions stack.

The product-level contract is not "researcher only." Researcher is the first high-value domain, but
the same sourcing service must accept records from `devpost`, `github`, researcher sources, and
future source families.

## Core Value

Turn heterogeneous scraping outputs into durable, reviewable, source-backed entities with explicit
reasoning, without forcing all source-specific payloads into SQL columns or rewriting working
Python scrapers into TypeScript.

## Current Milestone: v1.2 Sourcing Service And Human Review Foundation

**Goal:** Build a shared Firebase-backed sourcing service where local Python workers upload schema-validated source records, and core-service manages storage, evidence extraction, dedup candidates, human review, and approved entities.

**Target features:**
- Add a `sourcing` service to `wekruit-core-service-cloud-function` using the existing service layout: `domain`, `application`, `repositories`, `functions/http`, and `functions/tasks`.
- Define zod schemas and Firestore collection contracts for source runs, source records, evidence records, dedup candidates, review labels, and approved entities.
- Store large raw payloads through Cloud Storage pointers instead of forcing everything into Firestore documents.
- Expose core-service HTTP ingest endpoints that Python workers call instead of writing directly to Firebase.
- Add a Python ingest client in `wekruit-scraping` that can upload local JSONL/replay output to core-service.
- Integrate researcher sources (`OpenAlex`, `ORCID`, `DBLP`, `OpenReview`) as `domain=researcher` source records.
- Adapt existing scraping domains (`devpost`, `github`) to the same source-record contract.
- Create first-class evidence records for every merge-relevant signal, including source record ID, raw value, normalized value, value hash, extraction path, source URL, quality, and observed timestamp.
- Generate dedup candidates that reference evidence IDs and reason codes while requiring human review before any approved entity is created.
- Keep dedup inside the `sourcing` service as a domain/application submodule instead of creating a separate top-level service before the first review loop is proven.
- Reserve outbound as the downstream consumer of human-approved entities only; unresolved dedup candidates cannot become outbound candidates.

## Requirements

### Validated

- Official-source researcher ingest backbone exists for AI/ML-first paper and author discovery (Phase 1).
- Raw paper and author staging is replayable and audit-friendly through run manifests (Phase 1).
- OpenAlex is the working researcher ingest backbone and Crossref is the DOI backfill layer (Phase 1).
- AI/CS paper corpus gating exists with venue-tier decisions and include/exclude reason logs (Phase 6).
- Core-service already has Firebase Functions, Firestore, zod, repository patterns, task queues, emulator config, and centralized collection naming.

### Active

- [ ] Define sourcing schemas in core-service using zod, not ad hoc Firestore documents.
- [ ] Add Firestore collection names and indexes for sourcing records without disrupting existing `matching` and `outbound` services.
- [ ] Enforce `sourcing-*` Firestore collection prefixes, `sourcing/raw/...` Cloud Storage prefixes, `sourcing-*` task queue prefixes, and `/api/sourcing/...` HTTP route prefixes.
- [ ] Build HTTP ingest endpoints in core-service for source runs and source-record batch upserts.
- [ ] Keep Python scraping execution local or worker-based; Python calls the core-service API and does not directly own Firebase writes.
- [ ] Add a Python ingest client that validates/serializes source-record payloads and preserves local JSONL replay.
- [ ] Map researcher OpenAlex/ORCID/DBLP/OpenReview outputs into generic source records.
- [ ] Map existing `devpost` and `github` scraping outputs into the same generic source-record shape.
- [ ] Extract comparable evidence records and create dedup candidates with machine-readable reasoning.
- [ ] Require human review labels before creating approved entities.

### Out of Scope

- Rewriting Python scrapers into TypeScript Cloud Functions — this creates migration risk without solving sourcing correctness.
- Letting Python workers write directly to Firestore — schema, credentials, and review-state ownership must stay in core-service.
- Postgres for v1.2 — not aligned with the existing core-service Firebase stack or the schema-document requirement.
- MongoDB or another new document database — Firebase is already present.
- Neo4j as primary store — graph projection can be reconsidered later if traversal becomes a measured product need.
- Full reviewer UI — API/CSV/JSONL review loop is enough before product UI.
- Automatic merge without human approval — candidate strength is triage, not approval.
- Ranking, outreach, or recruiter export based on unreviewed identities.
- Writing unresolved dedup candidates into `outbound-candidates`.

## Context

`wekruit-scraping` currently contains multiple source domains:

- `devpost/`
- `github/`
- `researcher/`

The existing core-service repo already has the operational stack needed for product storage and
review workflows:

- Firebase Functions runtime
- Firestore repositories
- zod validation
- centralized collection registry
- Cloud Tasks pattern
- emulator and deploy scripts
- existing services organized as `matching` and `outbound`

Therefore, v1.2 should not add another database or another backend framework. The right integration
boundary is:

```text
Python scraping workers -> core-service sourcing ingest API -> Firebase storage/review workflow
```

Researcher remains the first domain with merge reasoning. The architecture must also support
Devpost projects, GitHub developers/repos, and future source families as generic source records.

## Constraints

- **Core-service owns persistence**: All durable product writes go through core-service APIs or tasks.
- **Python owns source execution**: Python workers keep fetching/parsing logic and local replay files.
- **Schema-first Firestore**: Firestore documents are validated through zod schemas in core-service.
- **Cloud Storage for large raw**: Large source payloads are stored by pointer, not forced into a single Firestore document.
- **No direct Firebase writes from Python**: Python should not carry Admin SDK credentials or bypass service validation.
- **Existing file-management pattern**: New core-service code follows existing `src/services/{service}/domain|application|repositories|functions` conventions.
- **Generic source record**: Do not hard-code the storage contract to researcher.
- **Evidence-first**: Review reasoning must reference durable evidence IDs, not only flattened strings or free-text reasons.
- **Human-reviewed merge**: Dedup candidates can be strong, medium, or weak, but no candidate becomes approved without a human label.
- **Dedup is not merge**: Dedup candidates are review proposals, not approved entities.
- **Reasoning required**: Every dedup candidate must preserve reason codes such as `email_exact`, `orcid_exact`, `github_exact`, `homepage_exact`, `paper_overlap`, or `name_institution`.
- **Ranking waits**: Ranking and outreach wait until approved entities exist.
- **Outbound waits**: Outbound integration consumes only approved entities with approved contact evidence.
- **Sourcing prefix required**: All sourcing-owned Firestore collections, task queues, and raw storage paths use explicit `sourcing` prefixes.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use core-service Firebase stack as storage/review backend | It already has Functions, Firestore, zod, repositories, tasks, and emulators | ✓ Good |
| Keep Python scrapers in `wekruit-scraping` | Existing Python source adapters work and should not be rewritten for storage reasons | ✓ Good |
| Python uploads through core-service API | Keeps schema validation, credentials, and product writes centralized | ✓ Good |
| Use generic `sourcing` service, not `researcher` backend | Current and future scraping domains need one ingestion/review contract | ✓ Good |
| Use Firestore + Cloud Storage pointers | Avoids SQL columns and supports heterogeneous source payloads | ✓ Good |
| Do not use Postgres for v1.2 | Conflicts with current Firebase backend and user preference against column management | ✓ Good |
| Do not use MongoDB | Adds a new database when Firebase already covers document storage | ✓ Good |
| Do not use Neo4j as primary store | Current bottleneck is review workflow and evidence, not graph traversal | ✓ Good |
| Keep dedup inside `sourcing` for v1.2 | Dedup only consumes source records/evidence and feeds review; a separate service boundary would add coordination before the first product loop exists | ✓ Good |
| Evidence is first-class | Human review needs auditable proof objects, not hidden extraction output | ✓ Good |
| Dedup candidates are separate from approved entities | The business requirement is explainable grouping, not automatic identity collapse | ✓ Good |
| All merge candidates require human review | The system can suggest, but only human labels approve identity collapse | ✓ Good |
| Outbound consumes approved entities only | Outreach should not act on unreviewed identity suggestions | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition**:
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone**:
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-15 after reframing v1.2 around sourcing service and Firebase/core-service integration*
