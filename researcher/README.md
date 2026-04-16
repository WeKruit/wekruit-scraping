# Researcher Pipeline

This directory is the third sourcing pipeline in the repo, alongside `devpost/` and `github/`.
It is being initialized as a standalone project for discovering researchers from official scholarly
data sources, linking them to papers and affiliations, and producing ranked, provenance-aware
contact candidates for WeKruit.

## What Lives Here

- `.planning/` — authoritative project docs created through the GSD initialization flow
- `docs/research_source_matrix_v2.xlsx` — standalone comparison sheet from the provided handoff
- `reference/p9-research-pipeline/` — preserved handoff package from `researcher_scraping.zip`

## Important Corrections To The Reference Package

The preserved handoff package is useful, but it should not be treated as production-ready without
review. Two assumptions need correction before implementation work starts:

1. ORCID should not be treated as a no-auth, always-safe source for a commercial pipeline.
   The current ORCID record-reading tutorial requires client credentials for Public API access,
   and ORCID documents that Public API terms are limited to non-commercial use cases. Commercial
   expert-finder usage may require Member API review and explicit credential planning.
2. OpenReview should be treated as a profile and homepage enrichment source, not an email source.
   It is useful for AI/ML identity resolution, but not as a reliable direct-contact database.

## Working Rule

The backbone for this pipeline is official scholarly APIs and dumps first. Generic web crawling is
allowed only as a secondary enrichment step after identity has already been resolved from trusted
sources.

## Local Sourcing Upload Bridge

The local Python worker remains the scraping/replay layer. It converts staged JSONL under
`data/runs/<run_id>/...` into generic `sourceRecord` payloads, then either writes a dry-run artifact
or uploads through the core-service sourcing API.

```bash
python scripts/s3_upload_source_records.py \
  --input-run poc-openalex-ai-2024 \
  --output-root data \
  --api-base-url http://127.0.0.1:5100/api/sourcing \
  --dry-run
```

Dry-run writes:

```text
data/runs/<run_id>/sourcing/source_run.json
data/runs/<run_id>/sourcing/source_records.jsonl
data/runs/<run_id>/sourcing/upload_summary.json
```

The bridge does not write Firestore directly. Non-dry-run mode calls:

```text
POST /api/sourcing/source-runs
POST /api/sourcing/source-records:batchUpsert
POST /api/sourcing/source-runs/:runId/complete
```

For local non-dry-run testing, start the core-service Hosting/Functions/Firestore
emulators together and use the Hosting rewrite URL:

```text
http://127.0.0.1:5100/api/sourcing
```

For Devpost, GitHub, or manual CSV/JSON/JSONL files, use the repo-level generic
uploader from the `wekruit-scraping` root:

```bash
python scripts/sourcing_upload_file.py \
  --input devpost/output/treehacks_complete.csv \
  --run-id devpost-treehacks-2026 \
  --domain hackathon \
  --source devpost \
  --api-base-url http://127.0.0.1:5100/api/sourcing

python scripts/sourcing_upload_file.py \
  --input github/output/candidates.json \
  --run-id github-ai-candidates-2026-04-15 \
  --domain developer \
  --source github \
  --api-base-url http://127.0.0.1:5100/api/sourcing
```

Use `--dry-run` first to produce replayable local artifacts under
`data/runs/<run_id>/sourcing/`.
