# v1.2 Sourcing Service Architecture

**Date:** 2026-04-15
**Milestone:** v1.2 Sourcing Service And Human Review Foundation

## Question

How should WeKruit connect existing Python scraping pipelines to durable storage, candidate
reasoning, human review, and approved entities without rewriting source collectors or forcing all
source payloads into SQL columns?

## Decision

Use the existing `wekruit-core-service-cloud-function` Firebase stack as the sourcing backend.

Keep Python scraping execution in `wekruit-scraping`. Python workers upload source-run and
source-record payloads through core-service HTTP ingest endpoints. Core-service validates the
payloads with zod and writes Firestore/Cloud Storage.

## Actual Core-Service Structure Observed

The core-service repository already follows this shape:

```text
src/bootstrap/
  firebase.ts
  secrets.ts

src/shared/
  firestore/collections.ts
  http/json.ts
  tasks/queueNames.ts
  validation/common.ts

src/services/matching/
  domain/
  application/
  integrations/
  repositories/
  functions/http/api.ts

src/services/outbound/
  domain/
  application/
  integrations/
  repositories/
  functions/http/api.ts
  functions/tasks/*.ts
```

The sourcing service must follow this existing file-management pattern. Do not introduce a new
framework or directory style.

Dedup should not be a separate top-level service in v1.2. It belongs inside `src/services/sourcing`
because it consumes sourcing records/evidence and feeds sourcing review labels. Split it internally by
domain/application files, not by another service boundary.

## Boundary

```text
wekruit-scraping
  Python workers
  source-specific API calls and scraping
  parsing and lightweight normalization
  local JSONL replay
  core-service ingest client

wekruit-core-service-cloud-function
  zod schemas
  Firestore collection registry
  Cloud Storage raw pointer contract
  repositories
  HTTP ingest API
  task queues
  evidence extraction
  dedup candidate generation
  review labels
  approved entities
```

## Why Not Move Python Into Core-Service

The source adapters already exist in Python and use Python-native libraries. Rewriting them in
TypeScript does not improve identity correctness or review workflow. It creates migration risk and
delays validation.

If Python workers need to move to cloud execution later, use Cloud Run Jobs after the HTTP ingest
contract is stable.

## Why Not Python Directly Writes Firebase

Python direct writes would:

- distribute Firebase credentials into scraping workers
- bypass core-service zod validation
- split product write ownership across repositories
- make schema evolution harder
- make review-state invariants easier to violate

The safer boundary is:

```text
Python -> core-service API -> Firebase
```

## Firebase Role

Firebase is not only a dumb storage layer. In v1.2, Firebase/core-service provides:

- Firestore document persistence
- Cloud Storage for large raw payloads
- zod schema validation before writes
- HTTP ingest API
- Cloud Tasks for async extraction/grouping/materialization
- review queue and label APIs
- approved entity materialization

The first implementation phase can focus on storage and ingest, but the architecture must preserve
the later review workflow.

## Source Record Contract

The storage contract should be generic, not researcher-specific:

```json
{
  "sourceRecordId": "openalex:A123",
  "domain": "researcher",
  "source": "openalex",
  "entityType": "person_profile",
  "runId": "run_001",
  "display": {
    "name": "Yann LeCun",
    "institution": "New York University"
  },
  "rawStoragePath": "sourcing/raw/researcher/openalex/run_001/A123.json",
  "rawSummary": {
    "orcid": "0000-0002-3192-2550",
    "worksCount": 412
  },
  "contentHash": "sha256:...",
  "schemaVersion": "sourcing_source_record.v1"
}
```

Examples:

- `domain=researcher`, `source=openalex`, `entityType=person_profile`
- `domain=hackathon`, `source=devpost`, `entityType=project_profile`
- `domain=developer`, `source=github`, `entityType=developer_profile`

## Core Collections

Recommended collection names:

```ts
export const sourcingCollections = {
  sourceRuns: 'sourcing-source-runs',
  sourceRecords: 'sourcing-source-records',
  evidence: 'sourcing-evidence',
  dedupCandidates: 'sourcing-dedup-candidates',
  reviewLabels: 'sourcing-review-labels',
  approvedEntities: 'sourcing-approved-entities',
} as const;
```

These should be added beside existing `matchingCollections` and `outboundCollections`, not as a
separate config mechanism.

## Firebase Prefix Contract

Sourcing-owned Firebase resources must be visually and operationally separated from existing
`matching` and `outbound` resources.

```ts
export const sourcingQueueNames = {
  extractEvidence: 'sourcing-extract-evidence',
  generateDedupCandidates: 'sourcing-generate-dedup-candidates',
  materializeApprovedEntity: 'sourcing-materialize-approved-entity',
} as const;
```

Raw payloads use this Cloud Storage prefix:

```text
sourcing/raw/{domain}/{source}/{runId}/{sourceRecordId}.json
```

HTTP routes use this route prefix:

```text
/api/sourcing/...
```

No sourcing-owned Firestore collection should use an unprefixed collection name. No scraping worker
should write directly to `outbound-*` collections.

## Evidence And Dedup Contract

Evidence is the durable proof object used by review and dedup. It is not only an extracted string.

Minimum evidence document:

```json
{
  "evidenceId": "ev_sha256_...",
  "domain": "researcher",
  "entityType": "person_profile",
  "sourceRecordId": "openalex:A123",
  "source": "openalex",
  "evidenceType": "orcid",
  "rawValue": "https://orcid.org/0000-0002-3192-2550",
  "normalizedValue": "0000-0002-3192-2550",
  "valueHash": "sha256:...",
  "extractedFrom": {
    "sourcePath": "authorships[0].author.orcid",
    "sourceUrl": "https://api.openalex.org/authors/A123"
  },
  "quality": "exact",
  "observedAt": "2026-04-15T00:00:00.000Z",
  "extractorVersion": "sourcing_evidence.v1"
}
```

Minimum dedup candidate document:

```json
{
  "dedupCandidateId": "dc_sha256_...",
  "domain": "researcher",
  "entityType": "person_profile",
  "sourceRecordIds": ["openalex:A123", "orcid:0000-0002-3192-2550"],
  "reasonCodes": ["orcid_exact"],
  "evidenceIds": ["ev_sha256_a", "ev_sha256_b"],
  "suggestedStrength": "strong",
  "status": "pending_review",
  "createdAt": "2026-04-15T00:00:00.000Z",
  "candidateVersion": "sourcing_dedup_candidate.v1"
}
```

Dedup candidates are proposals only. They can be strong enough to prioritize review, but they cannot
create approved entities without a human `same_person` label. Candidate IDs should be deterministic
from `domain`, `entityType`, source record IDs, and evidence hashes so repeat runs do not spam the
review queue.

## API Boundary

Minimum HTTP ingest API:

```text
POST /api/sourcing/source-runs
POST /api/sourcing/source-records:batchUpsert
POST /api/sourcing/source-runs/:runId/complete
```

Later review API:

```text
GET  /api/sourcing/dedup-candidates
GET  /api/sourcing/review-queue
POST /api/sourcing/review-labels
GET  /api/sourcing/approved-entities
```

Future outbound handoff API:

```text
POST /api/sourcing/approved-entities/:approvedEntityId/outbound-candidate
```

This is intentionally deferred until approved entities exist. The handoff target is the existing
`outbound-candidates` collection shape, not a direct write from scraping or dedup candidate records.

## Phase Strategy

1. Define core-service schemas and Firestore collections.
2. Implement core-service ingest API.
3. Add Python upload client and JSONL replay bridge.
4. Map researcher, Devpost, and GitHub outputs into the source-record contract.
5. Add evidence extraction and dedup candidate generation.
6. Add human review and approved entity materialization.

The full end-to-end product loop is specified in
`researcher/.planning/research/V1_2_SCRAPING_REVIEW_STORE_FLOW.md`.

## Final Call

The correct v1.2 architecture is:

```text
Local Python workers + JSONL replay
-> core-service sourcing HTTP ingest API
-> zod schema validation
-> Firestore + Cloud Storage
-> evidence extraction + dedup candidate generation
-> human review labels
-> approved entities
```

This keeps existing Python collectors intact while using the existing Firebase ecosystem for durable
storage and review workflow.
