# Stack Research — Milestone v1.1 AI/CS Ranking And Recruiter Readiness

**Scope:** Only the stack additions and source contracts needed to close the AI/CS-only ranking/export loop.
**Researched:** 2026-04-14
**Confidence:** Medium-high

## Mandatory Stack Additions

| Item | Type | Why this milestone needs it | Decision |
|------|------|-----------------------------|----------|
| AI/CS venue tier seed table | Local data asset (`csv` or `jsonl`) | Ranking corpus cannot be trusted without explicit venue gating | Required |
| OpenAlex author-detail fetch stage | Source adapter extension | Author influence needs stable source-native metrics, not guesses from authorships | Required |
| Canonical normalized paper/researcher artifacts | Pipeline stage output | Ranking and export should never read raw envelopes directly | Required |
| Ranking config / weight profile file | Local config asset | `latest` / `impact` / `balanced` must be explainable and versioned | Required |
| Recruiter export schema contract | Local schema/spec | Export has to preserve provenance and score breakdowns | Required |

## Keep Using

| Existing piece | Why it stays |
|----------------|-------------|
| Python 3.11+ flat scripts | Already matches repo shape and keeps execution/debugging cheap |
| JSONL staging | Replayable and good enough for this milestone |
| OpenAlex as ingest backbone | Already working and also provides author-detail APIs |
| Crossref as DOI metadata backfill | Still useful, but not the ranking backbone |

## External Source Contracts Needed Now

| Source | Milestone use | Need to verify/live-check | Notes |
|--------|---------------|---------------------------|-------|
| OpenAlex | papers, venue metadata, author details, citation metrics | API key, rate limits, author fields used for influence | Ranking depends on it directly |
| DBLP | AI/CS profile homepages | search/profile reliability and backoff behavior | Best as secondary profile enrichment, not corpus gate |
| ORCID | public profile URLs and occasional public email | credential/commercial path and field visibility | Useful but not mandatory for ranking itself |
| CCF directory | venue tier source of truth for AI/CS | mapping currency and licensing for local seed table | Human-curated reference |
| CORE / ICORE | venue tier source of truth for AI/CS | mapping currency and licensing for local seed table | Complements CCF coverage |

## Recommended File-Level Additions

```text
researcher/
├── data/
│   └── reference/
│       └── ai_cs_venue_tiers.csv
├── pipeline/
│   ├── canonical_schema.py
│   ├── normalization.py
│   ├── identity_graph.py
│   └── ranking.py
├── scripts/
│   ├── s2_author_detail_backfill.py
│   ├── s3_normalize_profiles.py
│   ├── s4_rank_papers.py
│   └── s5_export_ranked_outputs.py
└── config/
    └── ranking_profiles.example.py
```

## What Not To Add

| Avoid | Why |
|-------|-----|
| Pandas-first data layer | Overkill for staged pipeline size and obscures field provenance |
| Database migration in this milestone | Canonical shape is not stable enough yet |
| Generic crawler framework | Contradicts the official-source-first contract |
| UI/dashboard work | Not part of closing the AI/CS ranking loop |
| Bio/Pharma venue assets | Explicitly out of scope for this milestone |

## Concrete Data Assets

### `ai_cs_venue_tiers.csv`

Minimum columns:
- `venue_key`
- `display_name`
- `source_system`
- `source_grade`
- `normalized_tier`
- `domain_scope`
- `last_reviewed_at`
- `notes`

### `ranking_profiles.example.py`

Minimum profiles:
- `latest`
- `impact`
- `balanced`

Each profile should expose only:
- component weights
- recency half-life
- citation percentile rule
- venue unknown-handling rule

## Open Questions To Validate During Implementation

1. Which exact CCF and CORE snapshots are safe to encode into the local seed table?
2. Whether OpenAlex author-detail throughput is sufficient to backfill key authors inline or should be cached separately.
3. Whether DBLP profile fetch needs a persistent retry/backoff state or the current adapter-level throttling is enough.

## Sources

- OpenAlex Authentication / API overview: https://developers.openalex.org/guides/authentication and https://developers.openalex.org/api-reference/introduction
- CORE conference portal: https://portal.core.edu.au/conf-ranks/
- CCF recommendation directory updates: https://www.ccf.org.cn/Academic_Evaluation/By_category/ and public 2026 announcement context: https://04665u.npoall.com/news/itemid-238821.html
- Existing validated project docs under `.planning/`
