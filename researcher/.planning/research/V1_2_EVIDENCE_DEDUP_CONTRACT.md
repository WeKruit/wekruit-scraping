# v1.2 Evidence And Dedup Contract

**Date:** 2026-04-15
**Milestone:** v1.2 Sourcing Service And Human Review Foundation

## Decision

Do not create a separate top-level `dedup` service for v1.2.

Dedup lives inside `src/services/sourcing` as an internal domain/application layer:

```text
src/services/sourcing/
  domain/
    sourceRun.ts
    sourceRecord.ts
    evidence.ts
    dedupCandidate.ts
    reviewLabel.ts
    approvedEntity.ts
  application/
    ingestSourceRun.ts
    ingestSourceRecords.ts
    extractEvidence.ts
    generateDedupCandidates.ts
    applyReviewLabel.ts
    materializeApprovedEntity.ts
  repositories/
    sourcingRepository.ts
  functions/http/
    api.ts
  functions/tasks/
    extractEvidence.ts
    generateDedupCandidates.ts
```

Reason: dedup is not independently useful yet. It depends on source records, evidence, review labels,
and approved entities owned by the sourcing workflow. A separate service boundary can be revisited
only after the first review loop is live and painful enough to split.

## Core Invariant

Every merge suggestion must be traceable:

```text
sourceRecord -> evidence -> dedupCandidate -> reviewLabel -> approvedEntity
```

No approved entity can be created directly from source records, extracted strings, or suggested
strength. The only valid path is a human `same_person` review label on a dedup candidate.

## Firestore Collections

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

## Evidence Document

Evidence is a durable proof object. It is not just a normalized string on a candidate.

Required fields:

```ts
type SourcingEvidence = {
  evidenceId: string;
  domain: 'researcher' | 'developer' | 'hackathon' | string;
  entityType: string;
  sourceRecordId: string;
  source: string;
  evidenceType:
    | 'email'
    | 'orcid'
    | 'github'
    | 'homepage'
    | 'dblp_pid'
    | 'openreview_id'
    | 'google_scholar_id'
    | 'institution'
    | 'paper_doi'
    | 'source_native_id'
    | 'source_url';
  rawValue: string;
  normalizedValue: string;
  valueHash: string;
  extractedFrom: {
    sourcePath: string;
    sourceUrl?: string;
  };
  quality: 'exact' | 'normalized' | 'weak';
  observedAt: string;
  extractorVersion: string;
};
```

Deterministic ID:

```text
evidenceId = sha256(domain + entityType + sourceRecordId + evidenceType + normalizedValue + extractorVersion)
```

This makes reruns idempotent while still allowing extractor-version upgrades to create new evidence.

## Evidence Creation Rules

| Source | Evidence to create first | Quality |
|---|---|---|
| OpenAlex | `orcid`, `institution`, `paper_doi`, `source_native_id`, `source_url` | exact/normalized |
| ORCID | `email`, `homepage`, `institution`, `source_native_id`, `source_url` | exact |
| DBLP | `dblp_pid`, `homepage`, `source_native_id`, `source_url` | exact |
| OpenReview | `openreview_id`, `homepage`, `google_scholar_id`, `dblp_pid`, `source_url` | exact/normalized |
| GitHub | `github`, `email`, `homepage`, `source_native_id`, `source_url` | exact/normalized |
| Devpost | `homepage`, `github`, `source_native_id`, `source_url` | normalized/weak |

Email, ORCID, GitHub, DBLP PID, OpenReview ID, Google Scholar ID, and source-native IDs can create
strong dedup candidates. Homepage and institution alone should not create strong candidates.

## Dedup Candidate Document

Dedup candidates are human-review proposals.

Required fields:

```ts
type SourcingDedupCandidate = {
  dedupCandidateId: string;
  domain: string;
  entityType: string;
  sourceRecordIds: string[];
  evidenceIds: string[];
  reasonCodes: DedupReasonCode[];
  suggestedStrength: 'strong' | 'medium' | 'weak';
  status: 'pending_review' | 'same_person' | 'not_same_person' | 'unsure' | 'suppressed';
  createdAt: string;
  updatedAt: string;
  candidateVersion: string;
};
```

Deterministic ID:

```text
dedupCandidateId = sha256(domain + entityType + sorted(sourceRecordIds) + sorted(evidenceIds) + candidateVersion)
```

This prevents duplicate review spam across repeated runs.

## Reason Codes

| Reason code | Strength default | Rule |
|---|---:|---|
| `email_exact` | strong | Same normalized email across two or more source records |
| `orcid_exact` | strong | Same ORCID across two or more source records |
| `github_exact` | strong | Same normalized GitHub URL/login |
| `dblp_exact` | strong | Same DBLP PID |
| `openreview_exact` | strong | Same OpenReview profile ID |
| `google_scholar_exact` | strong | Same Google Scholar ID |
| `homepage_exact` | medium | Same normalized homepage URL |
| `paper_overlap` | medium | Same person-name candidate appears on overlapping DOI/paper evidence |
| `name_institution` | weak | Similar display name plus same normalized institution |

Each reason must reference one or more evidence IDs. A reason code without evidence IDs is invalid.

## Candidate Generation Rules

1. Group evidence by `(domain, entityType, evidenceType, normalizedValue)`.
2. Ignore groups with only one source record.
3. Create a dedup candidate for exact stable IDs first: email, ORCID, GitHub, DBLP, OpenReview, Google Scholar.
4. Create medium candidates for homepage/paper overlap only when at least two evidence records support the same pair.
5. Create weak candidates for name/institution only when no stronger candidate already exists for the same pair.
6. Suppress candidate creation when an existing review label says `not_same_person` or `unsure` for the same deterministic candidate unless new evidence changes the candidate ID.

## Human Review Rules

Human labels are stored separately in `sourcing-review-labels`.

Allowed labels:

```text
same_person
not_same_person
unsure
```

`same_person` can materialize or update an approved entity.

`not_same_person` and `unsure` suppress repeated review spam for the same deterministic candidate.

## Approved Entity Rules

Approved entities are review outputs, not source outputs.

Minimum approved entity record:

```ts
type SourcingApprovedEntity = {
  approvedEntityId: string;
  domain: string;
  entityType: string;
  sourceRecordIds: string[];
  evidenceIds: string[];
  reviewLabelIds: string[];
  display: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
};
```

No ranking, outreach, or recruiter export should use unresolved dedup candidates as if they were
approved entities.

## Phase Mapping

| Phase | Responsibility |
|---|---|
| Phase 11 | Define zod schemas, collection names, indexes, and fixtures for evidence/dedup/review/approved entities |
| Phase 12 | Persist source runs and source records only |
| Phase 13 | Upload local Python/JSONL source records to core-service |
| Phase 14 | Map OpenAlex, ORCID, DBLP, OpenReview, Devpost, and GitHub into source records |
| Phase 15 | Extract evidence and generate dedup candidates |
| Phase 16 | Review dedup candidates and materialize approved entities |

## Minimal POC

The first useful POC should prove this exact loop:

```text
OpenAlex author record with ORCID
ORCID public profile with same ORCID and homepage
-> two source records
-> two ORCID evidence records
-> one `orcid_exact` dedup candidate
-> manual `same_person` label
-> one approved researcher entity
```

If this loop works, adding DBLP/OpenReview homepage evidence is incremental rather than a new
architecture.
