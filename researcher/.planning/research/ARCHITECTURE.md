# Architecture Research — Milestone v1.1 AI/CS Ranking And Recruiter Readiness

**Scope:** Integration design for the current milestone only.
**Researched:** 2026-04-14
**Confidence:** High

## Build Order

```text
raw ingest
  -> corpus gate
  -> canonical normalization
  -> identity graph
  -> author-detail enrichment
  -> contact-quality enrichment
  -> explainable ranking
  -> recruiter export
```

## Required New Stages

### Stage A — Corpus Gate

**Input**
- staged OpenAlex `works_raw.jsonl`
- local `ai_cs_venue_tiers.csv`

**Output**
- `works_gated.jsonl`
- `works_excluded.jsonl`

**Responsibility**
- decide whether a paper is eligible for AI/CS ranking
- store `included_reason` or `excluded_reason`

### Stage B — Canonical Normalization

**Input**
- gated works
- staged raw authors
- Crossref backfill where available

**Output**
- canonical paper facts
- canonical author stubs
- paper-author edge facts

**Responsibility**
- convert source-native envelopes into one internal meaning
- preserve provenance on normalized fields

### Stage C — Identity Graph

**Input**
- canonical author stubs
- source IDs (OpenAlex, ORCID, DBLP, OpenReview when available)

**Output**
- resolved researcher profiles
- unresolved ambiguity queue

**Responsibility**
- merge only when stable-ID evidence is sufficient
- keep ambiguous candidates unmerged

### Stage D — Author Detail And Contact Enrichment

**Input**
- resolved researcher profiles
- key paper-author edges

**Output**
- enriched researcher metrics
- contact candidates with quality labels

**Responsibility**
- fetch OpenAlex author details for influence inputs
- attach ORCID/DBLP/OpenReview/homepage signals only after identity is stable

### Stage E — Explainable Ranking

**Input**
- canonical papers
- resolved/enriched researchers
- venue tiers
- ranking profile config

**Output**
- `ranked_papers.jsonl`
- `ranked_researchers.jsonl`

**Responsibility**
- compute component scores
- support `latest`, `impact`, and `balanced`
- emit component breakdowns

### Stage F — Recruiter Export

**Input**
- ranked canonical outputs

**Output**
- `ranked_papers.csv`
- `ranked_researchers.csv`

**Responsibility**
- flatten the ranked outputs for downstream sourcing use
- preserve enough provenance for trust and audit

## Integration Seams

| Seam | Why it matters |
|------|----------------|
| Raw ingest -> corpus gate | Prevents non-AI/CS papers from polluting all downstream stages |
| Corpus gate -> canonical normalization | Canonical schema should only model papers eligible for the milestone objective |
| Identity graph -> enrichment | Contact and influence must attach to stable people, not raw author mentions |
| Enrichment -> ranking | Ranking should consume explicit influence/contact-quality facts, not infer them ad hoc |
| Ranking -> export | Export should be a formatting layer, not a place that invents logic |

## Architectural Rules

1. Ranking never reads raw source envelopes directly.
2. Corpus gating happens before normalization and ranking.
3. Author influence is a separate enrichment pass, not buried inside ranking code.
4. Export is read-only over ranked artifacts.
5. Bio/Pharma stays out of the architecture for this milestone.

## Minimal Module Layout

```text
pipeline/
  corpus_gate.py
  canonical_schema.py
  normalization.py
  identity_graph.py
  ranking.py
  export.py

scripts/
  s2_author_detail_backfill.py
  s3_normalize_profiles.py
  s4_rank_outputs.py
  s5_export_outputs.py
```

## What To Avoid

- Directly modifying Phase 1 raw contracts just to support ranking
- Embedding venue-tier decisions inside source adapters
- Letting exporter code re-compute scores
- Building one mega-script that owns all stages
