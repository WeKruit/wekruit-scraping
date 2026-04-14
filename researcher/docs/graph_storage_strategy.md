# Graph Storage Strategy

**Date:** 2026-04-14
**Scope:** Multi-source researcher identity across 4 sources
**Decision owner:** P10 research synthesis

## Recommendation

Use **PostgreSQL as the system of record** for canonical identity, source-native profiles, and
append-only evidence. Do **not** start with Neo4j or another dedicated graph database as the
primary store for this project.

If graph-native traversal becomes a real hot path later, add **Neo4j as a projection layer**, not
as the initial source of truth.

## Why

This problem is primarily:

- identity resolution
- provenance tracking
- conflict preservation
- merge and unmerge safety
- auditability across runs and sources

That is a better fit for a relational core than for a graph-first core.

The hard problem is not “can we traverse a graph?” The hard problem is “when two source records
partially overlap, what evidence justifies a merge, and how do we reverse it safely later?” That
requires immutable observations and explicit merge history more than graph algorithms.

## Strategic Position

### Use Postgres first when

- the main workload is ingest, normalize, merge, rank, and export
- provenance and audit are mandatory
- merge/unmerge correctness matters more than path traversal
- current pipeline is still file-backed and Python-first
- the team wants the smallest operational surface

### Add Neo4j later only when

- multi-hop traversal becomes a frequent product query
- analyst exploration over person-paper-org-email paths becomes core
- graph algorithms or neighborhood search become part of the matching/ranking system
- relational joins are a measured bottleneck, not a hypothetical fear

## Recommended Model

### Canonical core

- `person`
  - internal canonical identity
- `source_profile`
  - one row per `(source_system, source_record_id)`
  - immutable source-native profile snapshot pointer
- `paper`
  - canonical work entity
- `organization`
  - canonical institution/entity

### Evidence layer

- `fact_evidence`
  - field name
  - normalized value
  - raw value
  - source system
  - source record id
  - observed timestamp
  - confidence / derivation rule
  - pointer to raw payload / run id

### Link layer

- `person_source_profile`
- `person_identifier`
- `person_paper`
- `person_organization`
- `person_email`
- `person_url`

### Merge history

- `merge_decision`
- `conflict`
- `unmerge_event`

## Data Rules

1. Raw source payloads remain append-only.
2. Source-native profiles remain immutable.
3. Canonical person fields are derived from evidence, not overwritten directly by source payloads.
4. Conflicting facts are preserved as competing evidence until resolved.
5. Merge must be evented and reversible.

## Practical Storage Shape

### Now

- JSONL raw staging remains the ingest/archive layer.
- Postgres becomes the durable canonical/evidence layer.
- Ranking/export read from Postgres after normalization and identity resolution mature.

### Later

- Optional Neo4j projection fed from canonical Postgres tables.
- Use it for traversal-heavy read paths only.

## Why Not Neo4j First

- adds a second operational system too early
- does not remove the need for merge discipline or provenance modeling
- encourages premature graph modeling before query patterns are proven
- makes the current file-backed to durable-store migration heavier than necessary

## If Neo4j Is Added Later

Use it as a projection with this shape:

- nodes: `Person`, `SourceProfile`, `Paper`, `Organization`, `Email`, `URL`, `Evidence`
- edges: `HAS_SOURCE_PROFILE`, `AUTHORED`, `AFFILIATED_WITH`, `IDENTIFIED_BY`, `ASSERTS`, `MERGED_INTO`

Keep provenance on evidence/assertion edges or nodes, not only on canonical person nodes.

## Migration Path

1. Keep current JSONL raw staging and run manifests.
2. Add Postgres loader for canonical/source/evidence tables.
3. Backfill historical runs from staged JSONL.
4. Build merge/unmerge logic in Postgres first.
5. Move downstream ranking/export reads onto Postgres.
6. Add Neo4j only if traversal-heavy use cases become real.

## Final Call

For the current stage of this repo, the correct architecture is:

**JSONL raw staging -> Postgres canonical + evidence store -> optional Neo4j projection later**

That is the shortest correct path with the best odds of preserving identity correctness,
provenance, and operational simplicity.
