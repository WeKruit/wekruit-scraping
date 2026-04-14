# Research Memo: Multi-Source Researcher Identity Storage

## Position

Model the same real-world person as a single internal `person` record, but never let that record absorb source-specific facts directly. Each source gets its own immutable `source_profile` snapshot, and every canonical field on `person` is derived from evidence, not overwritten by the latest source payload.

This is the safest way to handle partial and conflicting data from OpenAlex, ORCID, DBLP, and Crossref. The sources do not mean the same thing: OpenAlex and DBLP give disambiguated author entities, ORCID exposes user-controlled record sections with privacy constraints, and Crossref mostly contributes work-level metadata and identifiers rather than a stable person profile.

## Recommended Model

### Canonical identity vs source-native profiles

- `person`: internal canonical identity, stable across source changes.
- `source_profile`: one row per `(source_system, source_record_id)`, storing the source-native snapshot and raw payload pointer.
- `external_identifier`: normalized identifiers such as ORCID, OpenAlex author ID, DBLP PID, DOI-linked author metadata, with source and confidence metadata.

The canonical `person` should not be edited directly from source payloads. It should be updated only by merging evidence into a derived view.

### Provenance and evidence

Store facts as assertions, not as final truth:

- field name
- normalized value
- raw source value
- source system and source record id
- observed timestamp
- confidence / rank
- derivation rule
- pointer to raw JSONL or imported record

If two sources disagree, keep both assertions and let the canonical view choose a winner by rule. Never delete the losing evidence.

### Merge and unmerge

Merge must be an event, not a destructive rewrite.

- Auto-merge only on hard identifiers or very high-confidence matches.
- Keep merge reasons and a full lineage trail.
- Preserve source-native records even after merge.
- Support unmerge by splitting the canonical person into a new identity and replaying the evidence lineage.

This matters because source systems themselves can merge or redirect entities over time. OpenAlex redirects merged entities, and OpenAlex also documents a rare author-ID replacement during its 2023 author system upgrade. DBLP documents persistent author IDs that can merge or split. ORCID email visibility is private by default, so email cannot be treated as a stable identity anchor.

## If a Graph DB Is Chosen

Use the graph for relationship traversal, not as the only system of record.

### Node model

- `Person`
- `SourceProfile`
- `ExternalIdentifier`
- `Work`
- `Organization`
- `Evidence`

### Edge model

- `(:Person)-[:HAS_SOURCE_PROFILE]->(:SourceProfile)`
- `(:SourceProfile)-[:ASSERTS {field, confidence, observed_at}]->(:Evidence)`
- `(:Person)-[:IDENTIFIED_BY]->(:ExternalIdentifier)`
- `(:Person)-[:AUTHORED]->(:Work)`
- `(:Person)-[:AFFILIATED_WITH]->(:Organization)`
- `(:Person)-[:MERGED_INTO]->(:Person)`

Put provenance and confidence on the assertion edge or evidence node, not on the person node. Keep source profiles immutable so merges can be replayed or reversed.

## If a Graph DB Is Not Chosen

Use PostgreSQL as the system of record.

### Core tables

- `person`
- `source_profile` with unique `(source_system, source_record_id)`
- `external_identifier` with unique `(identifier_type, normalized_value)`
- `person_identifier`
- `person_fact`
- `fact_evidence`
- `merge_event`
- `work`
- `person_work`
- `organization`
- `person_affiliation`

Store raw imported source payloads in `jsonb`, but keep identity keys, merge events, and evidence rows relational. That gives strong constraints, easier backfills, and simpler unmerge logic than a file-only or graph-only design.

## Migration Path From File Pipeline

Keep JSONL as the ingest/staging layer, not as the long-lived canonical store.

1. Preserve the current raw JSONL output and run manifests.
2. Add a loader that upserts `source_profile`, `external_identifier`, and `fact_evidence`.
3. Backfill historical runs from staged JSONL files.
4. Recompute canonical identity links inside the durable store.
5. Switch downstream ranking and export reads to the database.
6. Leave files as raw audit/archive artifacts only.

Do not maintain two canonical output shapes. The durable store should become the single source of truth for identity and evidence; the files remain the replayable input history.

## Recommendation

Use PostgreSQL for the durable system of record, with a graph projection only if traversal-heavy matching becomes a real query bottleneck. That keeps merge/unmerge, provenance, and constraints straightforward while still preserving a path to graph-style exploration later.

## Primary Sources

- OpenAlex author docs: https://docs.openalex.org/api-entities/authors
- OpenAlex single entity merges and redirects: https://docs.openalex.org/how-to-use-the-api/get-single-entities
- ORCID record reading and visibility: https://info.orcid.org/documentation/api-tutorials/api-tutorial-read-data-on-a-record/
- ORCID email visibility defaults: https://support.orcid.org/hc/en-us/articles/360006894494-Visibility-preferences
- DBLP persistent author IDs and person records: https://dblp.org/faq/How%2Bto%2Bobtain%2Ball%2Bpersistent%2Bauthor%2BIDs%2Bfrom%2Bthe%2Bdblp%2Bxml
- Crossref REST API identifiers and affiliations: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- Neo4j graph model basics: https://neo4j.com/docs/getting-started/data-modeling/
- PostgreSQL JSONB and constraints: https://www.postgresql.org/docs/current/datatype-json.html and https://www.postgresql.org/docs/current/ddl-constraints.html
