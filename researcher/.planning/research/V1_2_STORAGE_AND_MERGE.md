# v1.2 Storage And Human Review Merge Research

**Date:** 2026-04-15
**Milestone:** v1.2 Four-Source Human Review Merge Foundation

## Question

How should the researcher pipeline store four source-profile pipelines and support human-reviewed
merge candidates with explicit reasoning?

## Short Answer

Use **Postgres as the primary durable store**.

Do not use NoSQL as the primary store. Do not use Neo4j as the primary store. Both can hold parts of
the data shape, but neither is the shortest correct path for human-reviewed identity merge.

## Why Postgres

The current problem is not generic document storage. The current problem is:

- four independently triggered source-profile pipelines
- source-native raw payload retention
- extracted comparable signals
- candidate groups with reason codes
- human labels
- negative and unsure review state
- approved researcher groups
- incremental suppression of already-reviewed candidates

That requires constraints, transactions, joins, uniqueness, review state, and audit history.
Postgres gives those directly while still supporting raw source payloads through JSONB.

## Why Not NoSQL Primary

NoSQL is attractive because each source payload has a different shape. That is real, but it solves
only the easiest part of the problem. The harder part is not storing one OpenAlex JSON blob. The
harder part is answering:

- which source profiles are in this candidate group?
- which signal created the group?
- who labeled it?
- was this pair already rejected?
- should this new run suppress or resurface the candidate?
- which approved person did this source profile join after review?

Those are relational review-state questions. A document store would force application-side joins
and make negative evidence harder to enforce.

## Why Not Neo4j Primary

Graph shape exists, but graph traversal is not the hot path yet. The immediate workflow is batch
ingest -> signal extraction -> candidate generation -> human review -> approved export.

Neo4j can become useful later for analyst exploration or graph algorithms, but using it first would
add operational surface area before the merge policy is stable.

## Recommended Storage Contract

### Core tables

- `source_runs`
  - one row per source pipeline run
- `source_profiles`
  - one row per `(source_system, source_record_id, run_id)`
  - stores raw payload in JSONB and normalized display fields in columns
- `profile_signals`
  - one row per extracted comparable signal
- `candidate_groups`
  - one row per generated review candidate group
- `candidate_group_profiles`
  - profiles participating in a candidate group
- `candidate_group_reasons`
  - machine-readable reasons such as `orcid_exact`, `email_exact`, `github_exact`, `homepage_exact`, `paper_overlap`
- `review_labels`
  - human labels: `same_person`, `not_same_person`, `unsure`
- `approved_people`
  - human-approved researcher groups
- `approved_person_profiles`
  - profiles attached to approved people

### Raw payload rule

Raw source payloads stay in JSONB on `source_profiles`. Do not flatten every source-native field
up front. Flatten only fields needed for joins, filters, review, and export.

### Human review rule

Candidate groups are never approved by strength alone. `suggested_strength` is only a triage hint.
Only a human `same_person` label can create or update an approved person group.

### Incremental rule

New pipeline runs can create new candidate groups. They must not repeatedly resurface a candidate
pair or group that already has a `not_same_person` or `unsure` label unless there is materially new
evidence.

## Four Pipeline Boundary

The four profile pipelines are:

1. OpenAlex
2. ORCID
3. DBLP
4. OpenReview

Homepage, GitHub, and email extraction are derived signal stages. They should write to
`profile_signals`, not become separate primary source systems for v1.2.

## Final Decision

The v1.2 durable store is:

```text
Postgres relational tables + JSONB raw payloads
```

The durable identity workflow is:

```text
source runs -> source profiles -> profile signals -> candidate groups + reasons -> human labels -> approved people
```

Neo4j remains a later read-model projection only if graph traversal becomes a measured product need.
