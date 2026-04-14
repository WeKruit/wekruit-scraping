# Phase 6: AI/CS Corpus Gate And Venue Tiers - Research

**Researched:** 2026-04-14
**Domain:** OpenAlex-based corpus gating with reviewed AI/CS venue tiers
**Confidence:** MEDIUM

<user_constraints>
## User Constraints

No `06-CONTEXT.md` exists yet. Constraints below are taken from the user request plus current roadmap/requirements.

### Locked Decisions
- Phase 6 must answer `CORPUS-01`, `CORPUS-02`, and `CORPUS-03`.
- AI/CS only. Bio/Pharma is out of scope.
- No UI or dashboard work.
- No generic crawl-first approach.
- Do not jump ahead into ranking formulas. This phase is only corpus gating and the venue-tier contract.
- Use the existing Phase 1 OpenAlex raw staging foundation as the input surface.
- Use first-principles reasoning and the shortest correct path only.
- Do not use compatibility-layer or bandaid plans.

### Claude's Discretion
- Define the exact venue-tier asset boundary, schema, provenance fields, and normalization rules.
- Define the gate contract over staged OpenAlex paper records.
- Define the incremental and auditability contract for reruns over time.
- Recommend plan slices for `06-01`, `06-02`, and `06-03`.

### Deferred Ideas (OUT OF SCOPE)
- Canonical schema and identity resolution
- Author/contact enrichment
- Ranking formulas, scoring weights, or mode design
- Recruiter export and calibration UI work
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CORPUS-01 | User can restrict the AI/CS ranking corpus to papers that pass explicit venue-tier inclusion rules. | Define a reviewed local venue asset, exact venue match precedence, allowed publication-form rules, and immutable gate outputs. |
| CORPUS-02 | User can review a local AI/CS venue-tier table that preserves upstream source, grade, normalized tier, and last-reviewed metadata. | Define `venue_tiers.csv` as the canonical review table, with explicit upstream provenance columns and local normalization fields. |
| CORPUS-03 | User can see why a paper was included or excluded from the AI/CS ranking corpus. | Define `paper_decisions.jsonl`, exact decision fields, and required inclusion/exclusion reason codes. |
</phase_requirements>

## Summary

Phase 6 should be implemented as a **pure local transform** over a completed Phase 1 OpenAlex run. The gate should consume a named `openalex/works_raw.jsonl` plus a committed, reviewed AI/CS venue asset, then emit two immutable outputs: one included corpus for downstream phases and one full decision ledger for audit. The gate must not call CCF or CORE at runtime.

The correct boundary is not "all concept-search results that look AI-like." The correct boundary is "papers whose publication venue can be deterministically matched to an explicitly reviewed AI/CS venue row that is marked ranking-eligible." OpenAlex discovery stays broad enough to find papers; Phase 6 is where that broad set becomes a defensible ranking corpus.

The main implementation detail that matters is venue identity. OpenAlex gives usable venue keys (`primary_location.source.id`, `locations.source.id`, `issn_l`, `issn`), but some real papers still arrive with `source: null` and only `raw_source_name`. Because of that, the asset boundary must include a small exact-match alias table in addition to the review table. Do not use fuzzy matching at runtime.

**Primary recommendation:** Commit a reviewed two-file venue asset (`venue_tiers.csv` + `venue_aliases.csv`), then gate each named OpenAlex run into `included_works.jsonl` and `paper_decisions.jsonl` using exact-match venue resolution and immutable asset fingerprints.

## Project Constraints (from CLAUDE.md)

- Use official scholarly APIs and dumps first. Generic crawling may appear only after identity resolution.
- Keep the implementation as a flat Python pipeline aligned with the existing repo; do not introduce a new framework.
- Preserve source provenance and quality state for every derived field.
- Keep scope AI/ML-first inside this repo; do not widen to broad all-domain ingest in this phase.
- Preserve operational resilience: replayable raw staging, rate limits, retries, and audit metadata remain mandatory patterns.
- Do not introduce a compatibility layer or multiple legacy shapes.
- Use GSD workflow entry points before making repo edits in execution work.

## Standard Stack

### Core
| Library / Format | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.11+ | Corpus gate implementation | Matches the current repo and existing Phase 1 scripts. |
| `csv` + `pathlib` + `json` + `hashlib` | stdlib | Asset loading, decision emission, asset fingerprinting | No new framework or storage layer is needed for this phase. |
| CSV | n/a | Human-reviewed venue asset | Reviewable, diffable, and easy to validate in tests. |
| JSONL | n/a | Input/output paper records and decision ledger | Matches the existing Phase 1 raw staging contract. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | 8.4.1 importable locally | Unit tests for asset validation and gate logic | Use for Phase 6 tests; the repo already uses pytest-style tests. |
| `requests` | `>=2.32` declared | One-time asset refresh helpers, if needed | Only for offline asset-refresh scripts, never for runtime gate logic. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Reviewed local asset snapshot | Live CCF/CORE lookups during gating | Rejected: nondeterministic, brittle, and breaks replay/audit. |
| Separate alias table | Fuzzy venue matching at runtime | Rejected: ambiguous and hard to test or explain. |
| Full rerun per upstream run | Mutable incremental corpus store | Rejected: unnecessary statefulness and weaker auditability for a local transform. |

**Installation:**
```bash
cd researcher
pip install -r requirements.txt
```

**Version verification:** No new package is required for Phase 6. Existing repo requirements currently declare `pyalex>=0.18`, `habanero>=1.2`, `requests>=2.32`, and `pytest>=9.0`, while the local environment reports Python `3.11.4` and `pytest` `8.4.1` importable.

## Architecture Patterns

### Recommended Project Structure
```text
researcher/
├── assets/
│   └── venue_tiers/
│       └── 2026-04-14/
│           ├── venue_tiers.csv      # Canonical venue review table
│           └── venue_aliases.csv    # Exact-match venue keys and aliases
├── pipeline/
│   └── corpus_gate.py               # Pure gate logic over staged OpenAlex work envelopes
├── scripts/
│   └── s6_corpus_gate.py            # Run gate for a named OpenAlex run
├── data/
│   └── runs/{gate_run_id}/corpus_gate/
│       ├── included_works.jsonl     # Included full work envelopes + gate annotations
│       ├── paper_decisions.jsonl    # One decision row per input work
│       └── summary.json             # Counts by decision/reason/venue/match type
└── tests/
    ├── test_phase6_venue_asset.py
    └── test_phase6_corpus_gate.py
```

### Pattern 1: Canonical Venue Review Table + Exact Alias Table
**What:** Keep the human review problem ("what is this venue and should it count?") separate from the record-attachment problem ("how do OpenAlex rows attach to that venue?").

**When to use:** Always. The local sample data already contains ranking-relevant works where `primary_location.source` is `null`, so one canonical table alone is not enough.

**Recommended asset boundary:**

`venue_tiers.csv` — one row per canonical venue

| Column | Required | Notes |
|--------|----------|-------|
| `venue_id` | yes | Stable local key, e.g. `conf/neurips`, `jour/jmlr` |
| `venue_type` | yes | `conference` or `journal` |
| `canonical_display_name` | yes | Human-review label |
| `canonical_abbreviation` | no | `NeurIPS`, `JMLR`, etc. |
| `normalized_tier` | yes | Local `T1`/`T2`/`T3`/`T4` |
| `include_in_corpus` | yes | Final explicit gate boolean; runtime consumes this, not a hard-coded threshold |
| `tier_decision_basis` | yes | `ccf_primary`, `core_only`, or `manual_review_conflict` |
| `ccf_area` | no | Usually `artificial-intelligence` in this phase |
| `ccf_grade` | no | `A`, `B`, `C` |
| `ccf_url` | no | Official page URL |
| `ccf_checked_at` | no | ISO-8601 |
| `core_source_edition` | no | e.g. `ICORE2026` |
| `core_rank` | no | `A*`, `A`, `B`, `C` |
| `core_url` | no | Search/export URL proving the row |
| `core_checked_at` | no | ISO-8601 |
| `last_reviewed_at` | yes | ISO-8601 |
| `last_reviewed_by` | yes | Reviewer identifier |
| `notes` | no | Manual review note only |

`venue_aliases.csv` — one row per exact match key

| Column | Required | Notes |
|--------|----------|-------|
| `venue_id` | yes | FK to `venue_tiers.csv` |
| `match_type` | yes | `openalex_source_id`, `issn_l`, `issn`, or `raw_source_name` |
| `match_value` | yes | Raw match key as stored |
| `match_value_normalized` | yes | For deterministic runtime lookup; identical to `match_value` for exact IDs/ISSNs |
| `source_system` | yes | `openalex`, `ccf`, `core`, or `manual_review` |
| `source_url` | no | Provenance URL for the alias evidence |
| `last_reviewed_at` | yes | ISO-8601 |

**Normalization rules:**
- `openalex_source_id`: store the full OpenAlex source URI exactly as OpenAlex emits it.
- `issn_l` and `issn`: uppercase, trim whitespace, preserve the canonical hyphen.
- `raw_source_name`: NFKC normalize, lowercase, replace `&` with `and`, strip a leading 4-digit year token, replace non-alphanumeric runs with a single space, collapse whitespace, trim. Match by exact equality after normalization only.
- No runtime fuzzy matching, edit distance, substring matching, or publisher-prefix heuristics.

**Recommended tier normalization:**
- `CCF A` -> `T1`
- `CCF B` -> `T2`
- `CCF C` -> `T3`
- `CORE/ICORE A*` -> `T1`
- `CORE/ICORE A` -> `T2`
- `CORE/ICORE B` -> `T3`
- `CORE/ICORE C` -> `T4`

**Rule for disagreements:** Preserve both upstream grades, but require the reviewer to set `normalized_tier` and `include_in_corpus` explicitly. Runtime code must never "average" or "pick the better rank" on the fly.

**Example:**
```python
# Source contracts:
# - OpenAlex Works/Sources docs: locations.source.id / issn / type
# - Local repo: researcher/pipeline/raw_staging.py
def normalize_source_name(value: str) -> str:
    import re
    import unicodedata

    text = unicodedata.normalize("NFKC", value or "").lower().replace("&", " and ")
    text = re.sub(r"^\d{4}\s+", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()
```

### Pattern 2: Pure OpenAlex Run -> Gate Run Transform
**What:** Gate only a named, completed OpenAlex run. Do not mutate raw files and do not treat `data/latest` as the authoritative input.

**When to use:** Every Phase 6 execution.

**Gate input contract:**
- Required input files:
  - `data/runs/{input_run_id}/run.json`
  - `data/runs/{input_run_id}/openalex/works_raw.jsonl`
- Consumed envelope fields:
  - `run_id`, `source_record_id`, `slice`, `fetched_at`, `checkpoint_cursor`, `page_number`
- Consumed OpenAlex raw fields:
  - `id`, `doi`, `display_name`/`title`, `publication_year`, `publication_date`
  - `type`, `is_retracted`, `is_paratext`
  - `primary_location.*`
  - `locations[*].is_published`, `locations[*].raw_type`, `locations[*].raw_source_name`, `locations[*].source.id`, `locations[*].source.issn_l`, `locations[*].source.issn`, `locations[*].source.type`
- Explicitly not consumed in Phase 6:
  - `authors_raw.jsonl`
  - Crossref backfill outputs
  - Ranking formulas or author influence fields

**Inclusion rules:**
1. Record must be an OpenAlex `works` envelope from the named input run.
2. Exclude immediately if `raw.is_retracted` or `raw.is_paratext` is true.
3. Build venue candidates from `primary_location` and then all `locations`.
4. Only consider candidate locations that are published (`is_published == true`) and whose publication form is `journal-article` or `proceedings-article`.
5. Resolve venue by exact match priority:
   - `openalex_source_id`
   - `issn_l`
   - `issn`
   - normalized `raw_source_name`
6. Resolve to exactly one `venue_id`. Multiple matches are an exclusion, not a guess.
7. Include only if the matched `venue_tiers.csv` row has `include_in_corpus = true`.

**Output contract:**
- `included_works.jsonl`: original OpenAlex work envelope plus a `corpus_gate` block
- `paper_decisions.jsonl`: one compact decision row per input work
- `summary.json`: counts by `decision`, `reason_code`, `venue_id`, `match_type`, and source slice

**Example:**
```python
# Source: repo Phase 1 envelope contract + OpenAlex works location fields
def candidate_locations(work_raw: dict) -> list[tuple[str, dict]]:
    values: list[tuple[str, dict]] = []
    primary = work_raw.get("primary_location") or {}
    if primary:
        values.append(("primary_location", primary))
    for index, location in enumerate(work_raw.get("locations") or []):
        values.append((f"locations[{index}]", location))
    return values
```

### Pattern 3: Full Decision Ledger, Not Just an Included Corpus
**What:** Emit one decision row for every input paper so exclusions stay inspectable.

**When to use:** Always. This is the direct answer to `CORPUS-03`.

**Required decision fields:**

| Field | Notes |
|------|-------|
| `gate_run_id` | Immutable gate run identifier |
| `input_run_id` | Named upstream OpenAlex run |
| `source_record_id` | OpenAlex work ID from the envelope |
| `doi` | Optional |
| `title` | For review |
| `publication_year` | For review |
| `decision` | `include` or `exclude` |
| `reason_codes` | Array of exact reason enums |
| `matched_venue_id` | Null when unmatched |
| `matched_alias_type` | `openalex_source_id`, `issn_l`, `issn`, `raw_source_name`, or null |
| `matched_location_ref` | `primary_location` or `locations[n]` |
| `normalized_tier` | Null when unmatched |
| `include_in_corpus` | Final gate bool |
| `venue_asset_version` | Reviewed asset version directory or tag |
| `venue_asset_fingerprint` | SHA-256 over asset files |
| `ruleset_version` | Gate code/version string |
| `decided_at` | ISO-8601 |

**Required exclusion reason codes:**
- `excluded_retracted`
- `excluded_paratext`
- `excluded_no_published_paper_location`
- `excluded_unsupported_publication_form`
- `excluded_missing_venue_identity`
- `excluded_unmapped_venue`
- `excluded_ambiguous_venue_match`
- `excluded_venue_not_ranking_eligible`

**Required inclusion reason codes:**
- `included_matched_openalex_source_id`
- `included_matched_issn_l`
- `included_matched_issn`
- `included_matched_raw_source_name`
- `included_venue_marked_ranking_eligible`

### Anti-Patterns to Avoid
- **Runtime CCF/CORE fetches:** breaks reproducibility and adds site fragility to a local transform.
- **Fuzzy venue rescue logic:** hides data quality problems and makes decisions hard to explain.
- **Using concept/keyword hits as the gate:** the requirement is explicit venue-tier inclusion, not text classification.
- **Letting `data/latest` drive audits:** convenience mirrors are not immutable inputs.
- **Mixing Phase 6 with ranking formulas:** this phase only decides corpus membership and venue-tier normalization.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Venue ranking source access | A live HTML scraper for CCF/CORE | A committed, reviewed CSV snapshot | Official pages can change, anti-bot protection exists, and replayability matters more than automation here. |
| Venue matching | Levenshtein or substring heuristics | Exact alias table with deterministic normalization | Avoids silent false positives like `ICML` vs `ICMLA`. |
| Corpus state | A mutable "current corpus" database | Immutable gate runs keyed by input run + asset fingerprint | Makes reruns auditable and diffs explainable. |
| AI/CS scope detection | An abstract/topic classifier over papers | Explicit venue-in-scope asset rows | Requirement is venue-tier gating, not semantic labeling. |

**Key insight:** The hard part of this phase is not file I/O. The hard part is making venue identity and corpus membership explicit enough that future ranking code never has to guess where a paper belongs.

## Incremental / Operational Contract

This phase does not need a mutable incremental store. The gate is a local, deterministic transform and should be rerun in full for each upstream OpenAlex run or asset revision.

**Recommended operational contract:**
- Input is always a named Phase 1 OpenAlex run ID, never an implicit "whatever is latest".
- A gate run is identified by:
  - `input_run_id`
  - `venue_asset_version`
  - `venue_asset_fingerprint`
  - `ruleset_version`
- Gate outputs are written to a new immutable run directory every time.
- A convenience `latest` mirror may exist, but it is not the audit source.
- If the venue asset changes, create a new gate run. Do not patch prior decision files in place.
- If a new OpenAlex run arrives, rerun the gate over that full run. Do not carry forward prior `include` decisions as mutable state.

**Why this is the shortest correct path:**
- Phase 6 is CPU-local and file-local. It is cheap enough to recompute.
- Mutable cross-run state would make it harder to answer "why is this paper in the corpus today but not yesterday?"
- The repo already treats raw upstream runs as replayable units. The gate should preserve that property.

## Common Pitfalls

### Pitfall 1: Matching only `primary_location.source.id`
**What goes wrong:** Valid conference papers are excluded because OpenAlex sometimes leaves `source` null even when `raw_source_name` still points to the venue.
**Why it happens:** Venue attachment in OpenAlex is not perfect for every work/location combination.
**How to avoid:** Use exact match priority across `source.id`, `issn_l`, `issn`, and normalized `raw_source_name`, with aliases reviewed locally.
**Warning signs:** Many exclusions with strong venue-like `raw_source_name` values such as `CVPR`, `ICLR`, or proceedings titles.

### Pitfall 2: Treating CORE as a journal authority
**What goes wrong:** Journal rows become incomplete or inconsistent because CORE/ICORE no longer maintains journal rankings.
**Why it happens:** CORE still has a conference portal, which can make it look like a full venue source.
**How to avoid:** Use CCF as the journal backbone in this phase; use CORE/ICORE only for conference provenance.
**Warning signs:** Empty journal coverage if the asset build starts from CORE alone.

### Pitfall 3: Letting repository or preprint records through
**What goes wrong:** arXiv or repository-hosted records enter the ranking corpus even when no ranked venue match exists.
**Why it happens:** OpenAlex discovery runs are intentionally broad and include repositories/preprints.
**How to avoid:** Require at least one matched published conference/journal location with an allowed publication form.
**Warning signs:** Included decisions with `source.type = repository` or `raw.type = preprint`.

### Pitfall 4: Reusing `latest` as if it were immutable
**What goes wrong:** Users cannot reproduce a previous corpus decision once `latest` has moved.
**Why it happens:** `latest` is convenient and already exists in Phase 1.
**How to avoid:** Require `--input-run` and record `parent_run_id`/`input_run_id` in every gate output.
**Warning signs:** Review notes or bugs that say "current latest" instead of a stable run ID.

### Pitfall 5: Folding conflicts into automatic tier math
**What goes wrong:** A venue with conflicting CCF/CORE evidence gets silently normalized without review.
**Why it happens:** It is tempting to encode a "best of both" rule.
**How to avoid:** Preserve upstream grades separately and require a reviewed `tier_decision_basis` for any disagreement.
**Warning signs:** Normalized tiers with no corresponding `ccf_grade`, `core_rank`, or manual note.

### Pitfall 6: Solving missing coverage with fuzzy matching instead of asset review
**What goes wrong:** Similar venue names collide and false positives enter the corpus.
**Why it happens:** Real venue strings vary by year, acronym, and proceedings title.
**How to avoid:** Exclude unmatched rows, then fix the asset. Do not "rescue" them with fuzzy logic.
**Warning signs:** Match rules that depend on edit distance, token overlap, or publisher-specific cleanup lists.

## Code Examples

Verified patterns from official sources and current repo contracts:

### Common Operation 1: Build deterministic venue keys from OpenAlex locations
```python
# Source:
# - https://developers.openalex.org/api-reference/works
# - researcher/pipeline/raw_staging.py
def iter_venue_keys(work_raw: dict) -> list[tuple[str, str, str]]:
    keys: list[tuple[str, str, str]] = []
    for location_ref, location in candidate_locations(work_raw):
        source = location.get("source") or {}
        if source.get("id"):
            keys.append((location_ref, "openalex_source_id", source["id"]))
        if source.get("issn_l"):
            keys.append((location_ref, "issn_l", source["issn_l"].strip().upper()))
        for issn in source.get("issn") or []:
            keys.append((location_ref, "issn", issn.strip().upper()))
        if location.get("raw_source_name"):
            keys.append((location_ref, "raw_source_name", normalize_source_name(location["raw_source_name"])))
    return keys
```

### Common Operation 2: Decide inclusion without mutating the upstream envelope
```python
# Source:
# - researcher/pipeline/run_context.py
# - researcher/pipeline/raw_staging.py
def build_decision(envelope: dict, venue_row: dict | None, match: dict | None, meta: dict) -> dict:
    raw = envelope.get("raw") or {}
    included = bool(venue_row and venue_row["include_in_corpus"])
    return {
        "gate_run_id": meta["gate_run_id"],
        "input_run_id": envelope["run_id"],
        "source_record_id": envelope["source_record_id"],
        "doi": raw.get("doi"),
        "title": raw.get("display_name") or raw.get("title"),
        "publication_year": raw.get("publication_year"),
        "decision": "include" if included else "exclude",
        "reason_codes": meta["reason_codes"],
        "matched_venue_id": None if not venue_row else venue_row["venue_id"],
        "matched_alias_type": None if not match else match["match_type"],
        "matched_location_ref": None if not match else match["location_ref"],
        "normalized_tier": None if not venue_row else venue_row["normalized_tier"],
        "include_in_corpus": included,
        "venue_asset_version": meta["venue_asset_version"],
        "venue_asset_fingerprint": meta["venue_asset_fingerprint"],
        "ruleset_version": meta["ruleset_version"],
        "decided_at": meta["decided_at"],
    }
```

### Common Operation 3: Annotate included work records for downstream phases
```python
def build_included_record(envelope: dict, decision: dict) -> dict:
    return {
        **envelope,
        "corpus_gate": {
            "decision": decision["decision"],
            "reason_codes": decision["reason_codes"],
            "matched_venue_id": decision["matched_venue_id"],
            "matched_alias_type": decision["matched_alias_type"],
            "normalized_tier": decision["normalized_tier"],
            "venue_asset_version": decision["venue_asset_version"],
            "venue_asset_fingerprint": decision["venue_asset_fingerprint"],
            "ruleset_version": decision["ruleset_version"],
        },
    }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Rank directly from broad concept/keyword discovery output | Gate discovery output through an explicit reviewed venue asset first | Phase 6 / 2026-04 | Corpus quality becomes explainable before any scoring happens. |
| One upstream grade or ad hoc venue labels | Preserve upstream grades separately and normalize locally with explicit review metadata | Current Phase 6 design | Avoids hiding source disagreements. |
| Live portal dependency for venue decisions | Commit a reviewed asset snapshot and fingerprint it | Current Phase 6 design | Makes reruns deterministic and audit-safe. |

**Deprecated/outdated:**
- OpenAlex `Concepts` are marked deprecated in the official docs. Phase 6 should not extend concept-based logic beyond consuming already staged Phase 1 runs; corpus membership should come from venue rules, not from concept IDs.

## Recommended Plan Slices

### 06-01: Define and review the AI/CS venue-tier asset and normalization contract
**Goal:** Commit the reviewed venue asset shape and validator before any gate code runs.

**Deliverables:**
- `assets/venue_tiers/{version}/venue_tiers.csv`
- `assets/venue_tiers/{version}/venue_aliases.csv`
- Asset schema validator
- Small reviewed seed set covering obvious milestone venues and explicit exclusions

**Scope recommendation:**
- Use the CCF AI page as the primary AI journal/conference backbone.
- Supplement missing AI conferences from the current ICORE conference edition when they are clearly in-scope for this milestone (for example, `ICLR` is present in ICORE2026 but not on the current CCF AI page).
- Do not widen to all CCF categories in this phase unless the planner explicitly locks broader CS scope first.

**Depends on:** Phase 1 only

### 06-02: Implement corpus gating over staged paper data
**Goal:** Turn a named OpenAlex run into an included corpus using the reviewed asset.

**Deliverables:**
- `pipeline/corpus_gate.py`
- `scripts/s6_corpus_gate.py`
- `included_works.jsonl`
- `summary.json`

**Rules to implement first:**
- Named input run only
- Exact venue match precedence
- Publication-form rules
- Immutable output directories with asset fingerprint and ruleset version

**Depends on:** `06-01`

### 06-03: Emit inclusion/exclusion reasons for every gated paper record
**Goal:** Make every include/exclude decision inspectable and stable.

**Deliverables:**
- `paper_decisions.jsonl`
- Reason-code enum contract
- Review-friendly summary counts by reason and venue
- Tests that assert decision coverage for every input work

**Depends on:** `06-01`, `06-02`

## Open Questions

1. **How broad is "AI/CS" for this milestone in practice?**
   - What we know: current ingest presets are AI/ML-centric; the roadmap says AI/CS, not all-CS.
   - What's unclear: whether Phase 6 should stay on the CCF AI area plus targeted supplements, or whether it should widen into additional CCF subareas now.
   - Recommendation: lock the Phase 6 asset boundary to `CCF AI + reviewed ICORE supplements` unless the planner gets an explicit requirement for broader CS coverage.

2. **What is the corpus floor for explicit `include_in_corpus`?**
   - What we know: the asset can preserve `normalized_tier` separately from the final inclusion boolean.
   - What's unclear: whether the milestone wants `T1-T3` included by default, or a stricter floor.
   - Recommendation: set `include_in_corpus` explicitly per row during 06-01 review and avoid coding a hidden global threshold in 06-02.

3. **How should ambiguous proceedings variants be handled?**
   - What we know: conference families often have workshops, companion volumes, and renamed editions.
   - What's unclear: whether some variants should share the main venue row or be excluded.
   - Recommendation: treat workshop/companion variants as separate rows or separate exclusions in the asset; never collapse them at runtime.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest` style tests; `pytest` 8.4.1 is importable locally |
| Config file | none |
| Quick run command | `python3 -m pytest tests/test_phase6_venue_asset.py tests/test_phase6_corpus_gate.py -q` |
| Full suite command | `python3 -m pytest tests -q` |

**Note:** In this environment, direct pytest CLI execution crashed before output. The repo still clearly uses pytest-style tests, so the commands above are the intended validation contract for planning.

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CORPUS-01 | Only venue-eligible papers enter the downstream corpus | unit | `python3 -m pytest tests/test_phase6_corpus_gate.py::test_includes_only_ranking_eligible_venues -q` | ❌ Wave 0 |
| CORPUS-02 | Local venue table preserves upstream grades, normalized tier, and review metadata | unit | `python3 -m pytest tests/test_phase6_venue_asset.py::test_asset_schema_and_required_provenance -q` | ❌ Wave 0 |
| CORPUS-03 | Every paper gets an explainable include/exclude reason | unit | `python3 -m pytest tests/test_phase6_corpus_gate.py::test_emits_decision_for_every_input_record -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/test_phase6_venue_asset.py tests/test_phase6_corpus_gate.py -q`
- **Per wave merge:** `python3 -m pytest tests -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_phase6_venue_asset.py` — validates CSV schema, required columns, tier normalization, and alias normalization
- [ ] `tests/test_phase6_corpus_gate.py` — validates include/exclude decisions and match precedence
- [ ] `tests/fixtures/corpus_gate/` — sample OpenAlex work envelopes, asset rows, and expected decision outputs

## Sources

### Primary (HIGH confidence)
- Repo contracts:
  - `researcher/pipeline/raw_staging.py` - raw envelope and append-only JSONL contract
  - `researcher/pipeline/run_context.py` - run manifest and immutable run layout
  - `researcher/scripts/s1_openalex_fetch.py` - Phase 1 OpenAlex ingest contract
  - `researcher/tests/test_phase1_contracts.py` and `researcher/tests/test_openalex_ingest.py` - current contract assertions
  - `researcher/data/latest/openalex/works_raw.jsonl` - observed local raw-work edge cases (`source: null`, repositories, preprints)
- OpenAlex official docs:
  - https://developers.openalex.org/api-reference/works - work fields, `locations.*`, `primary_location.*`, `primary_topic.*`
  - https://developers.openalex.org/api-reference/sources - source fields, `issn_l`, source types, and note that concepts are deprecated
- CCF official AI venue page:
  - https://www.ccf.org.cn/Academic_Evaluation/AI/ - official AI conference/journal list and grades
- CORE/ICORE official portal:
  - https://portal.core.edu.au/conf-ranks/ - conference portal and current source editions
  - https://portal.core.edu.au/conf-ranks/?search=NeurIPS&by=all&source=ICORE2026&do=Export - exportable official conference row example
  - https://portal.core.edu.au/conf-ranks/?search=ICLR&by=all&source=ICORE2026&do=Export - exportable official conference row example
  - https://docs.google.com/document/d/11lyr_N7rnyhpvTnGJRVvrFIp73REt3lwTCmy0k8geJo/export?format=txt - official FAQ, including that journal rankings were discontinued

### Secondary (MEDIUM confidence)
- None needed beyond the repo and official sources above.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new framework is required and the repo shape is already clear.
- Architecture: MEDIUM - the gate contract is clear, but the exact AI/CS venue boundary still needs one planning decision.
- Pitfalls: MEDIUM - grounded in official docs plus local sample data, but coverage edge cases will expand once a larger asset is reviewed.

**Research date:** 2026-04-14
**Valid until:** 2026-05-14
