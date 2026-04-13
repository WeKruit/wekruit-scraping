# Architecture Research

**Domain:** Academic researcher sourcing pipeline
**Researched:** 2026-04-13
**Confidence:** MEDIUM

## Standard Architecture

### System Overview

```text
┌──────────────────────────────────────────────────────────────┐
│                    Source Adapters Layer                    │
├──────────────────────────────────────────────────────────────┤
│  OpenAlex   Crossref   OpenReview   DBLP   ORCID   PubMed   │
└───────────────┬───────────────┬───────────────┬──────────────┘
                │               │               │
                ▼               ▼               ▼
┌──────────────────────────────────────────────────────────────┐
│                     Raw Staging Layer                       │
├──────────────────────────────────────────────────────────────┤
│      source-native JSONL + query metadata + replay state    │
└───────────────┬──────────────────────────────────────────────┘
                ▼
┌──────────────────────────────────────────────────────────────┐
│              Canonical Normalization / Identity             │
├──────────────────────────────────────────────────────────────┤
│ researcher schema   stable ID linking   conservative merge  │
└───────────────┬──────────────────────────────────────────────┘
                ▼
┌──────────────────────────────────────────────────────────────┐
│                    Enrichment Layer                         │
├──────────────────────────────────────────────────────────────┤
│ ORCID/contact data   homepage signals   quality labels      │
└───────────────┬──────────────────────────────────────────────┘
                ▼
┌──────────────────────────────────────────────────────────────┐
│                    Ranking / Export Layer                   │
├──────────────────────────────────────────────────────────────┤
│ recruiter score   ranked CSV/JSONL   source lineage output  │
└──────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Source adapters | Fetch source-native paper/author/profile data | One adapter per source with explicit request and parse logic |
| Raw staging | Preserve replayable upstream records | Timestamped JSONL files plus latest snapshots |
| Normalization layer | Convert source-native shapes into one canonical schema | Flat Python functions, not framework-heavy abstractions |
| Identity merge | Link or split researchers conservatively | Stable-ID-first merge rules, ambiguity left unresolved |
| Enrichment layer | Attach public contact and affiliation hints | Secondary passes after identity is already stable |
| Ranking/export | Produce recruiter-facing outputs | Deterministic scoring + CSV/JSONL exports |

## Recommended Project Structure

```text
researcher/
├── researcher_config.py        # env vars, paths, source registry, limits
├── researcher_pipeline.py      # top-level CLI / orchestration
├── researcher_discover.py      # raw ingest + merge entry point
├── sources/                    # source adapters only
│   ├── openalex_source.py
│   ├── crossref_source.py
│   ├── orcid_source.py
│   └── ...
├── output/                     # runtime artifacts
├── reference/                  # preserved handoff package
└── .planning/                  # project docs and roadmap
```

### Structure Rationale

- **Flat top level:** Matches the current repo’s script-oriented shape and keeps the shortest path clear.
- **`sources/` boundary:** Gives each upstream source a clean adapter without over-fragmenting the rest of the pipeline.
- **`reference/` separation:** Keeps prior handoff code visible without confusing it with the production path.

## Architectural Patterns

### Pattern 1: Source-native first, canonical second

**What:** Each adapter writes source-native data before canonical merge.
**When to use:** Always, because source contracts will change.
**Trade-offs:** Slightly more storage, much better replayability and auditability.

### Pattern 2: Stable-ID-first identity merge

**What:** ORCID/OpenAlex/DBLP-style identifiers outrank names.
**When to use:** Every merge path.
**Trade-offs:** Leaves some profiles unresolved, but prevents wrong merges.

### Pattern 3: Secondary crawling only after identity resolution

**What:** Homepage parsing is a narrow enrichment step, not the ingest backbone.
**When to use:** Only when trusted sources have already identified the researcher.
**Trade-offs:** Lower early coverage, much better correctness.

## Data Flow

### Request Flow

```text
CLI run
    ↓
researcher_pipeline.py
    ↓
source adapter(s)
    ↓
raw JSONL staging
    ↓
canonical normalization
    ↓
identity merge
    ↓
enrichment / quality labels
    ↓
ranked export
```

### Key Data Flows

1. **Ingest flow:** source query → raw source-native records → canonical staging.
2. **Identity flow:** canonical records → stable-ID matching → merged researcher profile.
3. **Contact flow:** merged profile → ORCID/profile/homepage enrichment → quality-labeled contacts.
4. **Export flow:** merged profile → scoring → CSV/JSONL output for recruiting.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Early validation | File-based JSONL staging is sufficient |
| Larger source volume | Add better incremental checkpoints and source partitioning |
| Mature production | Move normalized artifacts into a database only after schema is stable |

### Scaling Priorities

1. **First bottleneck:** source-rate-limit coordination — solve with explicit per-source throttling and replay.
2. **Second bottleneck:** merge correctness — solve with better stable-ID coverage before optimizing throughput.

## Anti-Patterns

### Anti-Pattern 1: Merge while ingesting

**What people do:** Deduplicate directly inside source fetch loops.
**Why it's wrong:** It hides source-native truth and makes replay/debugging painful.
**Do this instead:** Stage raw first, merge second.

### Anti-Pattern 2: Build the contact waterfall before the identity graph

**What people do:** Chase emails before researcher identity is stable.
**Why it's wrong:** Contacts attach to the wrong person and pollute trust.
**Do this instead:** Make identity correctness the gate to contact enrichment.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| OpenAlex | Primary ingest adapter | Backbone for papers/authors |
| Crossref | Metadata backfill adapter | Use polite pool with identification |
| ORCID | Credentialed enrichment adapter | Commercial usage and credential mode must be validated |
| DBLP | Author/publication enrichment adapter | Use API/XML/JSON endpoints, not HTML scraping |
| NCBI E-utilities | Targeted biomedical adapter | Only for bio-specific expansion |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| adapters ↔ staging | JSONL files | Makes reruns explicit |
| staging ↔ normalization | canonical record transforms | Keep one schema meaning |
| normalization ↔ export | merged researcher profiles | Ranking must not rewrite source truth |

## Sources

- OpenAlex developer docs
- Crossref REST API docs
- ORCID record-reading tutorial
- DBLP XML Requests documentation
- NCBI E-utilities documentation

---
*Architecture research for: academic researcher sourcing pipeline*
*Researched: 2026-04-13*
