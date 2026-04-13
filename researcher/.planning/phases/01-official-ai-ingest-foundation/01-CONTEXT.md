# Phase 1 Context: Official AI Ingest Foundation

## Title
Phase 1: Official AI Ingest Foundation

## Objective
Deliver a replayable, AI/ML-first ingest backbone that pulls paper and author records from official scholarly sources, preserves raw source-native payloads, and records enough run metadata to support audit, replay, and incremental reruns.

## Phase Boundary
This phase is only about ingest foundation.

Included:
- Source config surface for official scholarly ingest
- Source registry and source-aware run metadata
- Raw staging contract for papers, authors, and source responses
- OpenAlex-led paper/author ingest
- AI/ML query presets for concept, venue, and keyword entrypoints
- Crossref metadata backfill for DOI-enriched paper metadata
- Replay and incremental controls for reruns

Explicitly excluded:
- Canonical schema and merge logic
- Identity resolution across sources
- ORCID, OpenReview, DBLP, homepage, PubMed, or any contact enrichment
- Ranking, export, dashboards, or operator UI
- Generic crawling of websites or homepages

## Repo Alignment
The root repo uses flat Python entrypoints in sibling pipelines:
- `github/` uses one config module plus flat stage modules and one orchestrator
- `devpost/` is source-specific and script-driven

Phase 1 should follow the cleaner `github/` pattern inside `researcher/`:
- one config module
- one source registry module
- one raw staging / run-state module
- one OpenAlex adapter
- one Crossref adapter
- one orchestrator entrypoint

Do not introduce a framework, queue, database, or multi-layer package structure in this phase.

## Deliverable Shape
By the end of Phase 1, the executor should leave `researcher/` with a minimal but complete ingest surface like:
- `researcher/researcher_config.py`
- `researcher/researcher_sources.py`
- `researcher/researcher_run_state.py`
- `researcher/researcher_openalex.py`
- `researcher/researcher_crossref.py`
- `researcher/researcher_pipeline.py`
- `researcher/tests/` for phase-1 verification

The runtime artifact shape should be deterministic and replayable:
- `researcher/data/runs/<run_id>/run.json`
- `researcher/data/runs/<run_id>/openalex/papers_raw.jsonl`
- `researcher/data/runs/<run_id>/openalex/authors_raw.jsonl`
- `researcher/data/runs/<run_id>/crossref/papers_backfill_raw.jsonl`
- `researcher/data/runs/<run_id>/checkpoints/*.json`
- `researcher/data/latest/*.jsonl` or manifest pointers for the most recent successful run

## Plan Split
Phase 1 is intentionally split into three executable plans with one correctness boundary each.

### 01-01: Config / Registry / Run Metadata / Raw Staging
Purpose:
- define the ingest contract before any source logic is added
- prevent OpenAlex and Crossref from inventing incompatible output shapes

Produces:
- config model
- source registry
- run manifest schema
- raw staging writer/reader contract

### 01-02: OpenAlex-Led Ingest And AI/ML Query Presets
Purpose:
- implement the actual AI/ML-first discovery path
- make OpenAlex the phase-1 ingest backbone

Produces:
- OpenAlex adapter
- venue/concept/keyword presets
- paper/author raw outputs tied to run metadata

### 01-03: Crossref Backfill And Replay / Incremental Controls
Purpose:
- add DOI-driven paper metadata backfill without changing the raw contract
- make reruns deterministic and resumable

Produces:
- Crossref backfill step
- replay mode and checkpoint rules
- incremental fetch logic for same preset / newer publication windows

## Execution Order
Plans must execute in order:
1. `01-01-PLAN.md`
2. `01-02-PLAN.md`
3. `01-03-PLAN.md`

`01-02` must consume the contracts defined in `01-01`.
`01-03` must extend those contracts without redefining them.

## Requirement Mapping
- `INGEST-01`: covered by OpenAlex and Crossref official-source ingest
- `INGEST-02`: covered by AI/ML concept, venue, and keyword presets
- `INGEST-03`: covered by raw staging contract plus replay controls
- `QUALITY-02`: covered by run metadata, retries, limits, checkpoints, and incremental reruns

## Phase Done Criteria
Phase 1 is ready to mark complete only when all of the following are true:
- A user can run one AI/ML preset through `researcher/researcher_pipeline.py` without generic crawling
- OpenAlex raw paper and author payloads are written under a run-scoped directory with run metadata
- Crossref can backfill DOI-linked paper metadata into the same run without overwriting OpenAlex raw files
- The same run configuration can be replayed from staged raw files without a network call
- Incremental reruns write a new run manifest while preserving prior run artifacts
- Limits, retries, and checkpoint state are source-aware and recorded in run metadata

## Risks And Dependencies
- OpenAlex query semantics must be pinned carefully so concept / venue / keyword presets are reproducible
- Crossref backfill depends on DOI presence and must not become a discovery path
- Live rate limits and polite client requirements must be confirmed from official docs during execution
- The raw staging contract must stay source-native; if the executor normalizes here, Phase 2 will be polluted
