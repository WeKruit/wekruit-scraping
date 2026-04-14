# Phase 6 POC Results

**Date:** 2026-04-14
**Scope:** Local proof-of-concept runs for the AI/CS corpus gate

This document records the real local runs executed against staged OpenAlex data after Phase 6
shipped. The goal is to show what the gate includes, what it excludes, and how rerun semantics
behave when the venue asset changes.

## POC 1 — Gate an existing OpenAlex AI run

**Command**

```bash
cd /Users/adam/Desktop/WeKruit/wekruit-scraping/researcher
. .venv/bin/activate
python scripts/s2_corpus_gate.py \
  --input-run poc-openalex-ai-2024 \
  --run-id poc-corpus-gate-ai-2024
```

**Outputs**

- `/Users/adam/Desktop/WeKruit/wekruit-scraping/researcher/data/runs/poc-corpus-gate-ai-2024/corpus_gate/run.json`
- `/Users/adam/Desktop/WeKruit/wekruit-scraping/researcher/data/runs/poc-corpus-gate-ai-2024/corpus_gate/gated_works.jsonl`
- `/Users/adam/Desktop/WeKruit/wekruit-scraping/researcher/data/runs/poc-corpus-gate-ai-2024/corpus_gate/gate_decisions.jsonl`

**Observed result**

- Included: `1`
- Excluded: `2`
- Included sample:
  - `Artificial intelligence in education: A systematic literature review`
  - Venue: `Expert Systems with Applications`
  - Tier: `T3`
- Excluded sample 1:
  - `A Perspective on Explainable Artificial Intelligence Methods: SHAP and LIME`
  - Venue: `Advanced Intelligent Systems`
  - Reason: `venue_row_unresolved`
- Excluded sample 2:
  - `Revised Surgical CAse REport guidelines`
  - Venue: `Premier journal of science.`
  - Reason: `source_not_in_ai_cs_table`

## POC 2 — Gate a broader staged AI run

**Command**

```bash
cd /Users/adam/Desktop/WeKruit/wekruit-scraping/researcher
. .venv/bin/activate
python scripts/s2_corpus_gate.py \
  --input-run poc-openalex-ai-2024-10 \
  --run-id poc-corpus-gate-ai-2024-10
```

**Outputs**

- `/Users/adam/Desktop/WeKruit/wekruit-scraping/researcher/data/runs/poc-corpus-gate-ai-2024-10/corpus_gate/run.json`
- `/Users/adam/Desktop/WeKruit/wekruit-scraping/researcher/data/runs/poc-corpus-gate-ai-2024-10/corpus_gate/gated_works.jsonl`
- `/Users/adam/Desktop/WeKruit/wekruit-scraping/researcher/data/runs/poc-corpus-gate-ai-2024-10/corpus_gate/gate_decisions.jsonl`

**Observed result**

- Included: `0`
- Excluded: `10`
- Representative exclusions:
  - `Dagstuhl Research Online Publication Server` -> `source_not_in_ai_cs_table`
  - `DROPS-IDN/LIPI` -> `source_not_in_ai_cs_table`
  - `Attention Is All You Need` sample with no resolved primary source -> `missing_primary_source`

This run is useful because it proves the gate is strict. A broad concept-oriented upstream sample
does not become AI/CS corpus material unless the venue row is explicit and reviewed.

## POC 3 — Rerun semantics after asset revision

**Command**

```bash
cd /Users/adam/Desktop/WeKruit/wekruit-scraping/researcher
. .venv/bin/activate
python scripts/s2_corpus_gate.py \
  --input-run poc-openalex-ai-2024 \
  --venue-table data/poc_assets/ai_cs_venue_tiers_revalidated.csv \
  --run-id poc-corpus-gate-ai-2024-revalidated
```

**Outputs**

- `/Users/adam/Desktop/WeKruit/wekruit-scraping/researcher/data/runs/poc-corpus-gate-ai-2024-revalidated/corpus_gate/run.json`
- `/Users/adam/Desktop/WeKruit/wekruit-scraping/researcher/data/runs/poc-corpus-gate-ai-2024-revalidated/corpus_gate/gated_works.jsonl`
- `/Users/adam/Desktop/WeKruit/wekruit-scraping/researcher/data/runs/poc-corpus-gate-ai-2024-revalidated/corpus_gate/gate_decisions.jsonl`

**Observed result**

- Included: `1`
- Excluded: `2`
- Same corpus decision as POC 1
- Different venue-table fingerprint in `run.json`

This proves the rerun contract is append-only. A new gate run is created for a new asset revision
instead of mutating the old result set in place.

## What these POCs prove

1. The corpus gate is real and executable over staged OpenAlex runs, not just a planning artifact.
2. Inclusion is driven only by explicit reviewed AI/CS venue rows.
3. Every exclusion has a machine-readable reason in `gate_decisions.jsonl`.
4. Asset revisions produce new append-only gate runs with lineage, not destructive overwrites.

## What these POCs do not prove yet

1. Alias-based venue matching beyond exact OpenAlex source ID.
2. Continuous scheduled ingestion of new papers.
3. Canonical person identity resolution across multiple sources.
4. Recruiter-facing ranking or export correctness.
