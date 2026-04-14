from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

from pipeline.raw_staging import stage_records
from pipeline.run_context import (
    build_derived_run_manifest,
    write_derived_run_manifest,
)
from pipeline.venue_tiers import (
    DEFAULT_VENUE_TIER_ASSET,
    hash_venue_tier_asset,
    VenueTierRow,
    load_venue_tiers,
    matched_ai_cs_venue_tier,
    missing_primary_source,
    source_not_in_ai_cs_table,
    venue_explicitly_excluded,
    venue_row_unresolved,
)


STAGE_NAME = "corpus_gate"
GATED_WORKS_FILENAME = "gated_works.jsonl"
GATE_DECISIONS_FILENAME = "gate_decisions.jsonl"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _resolve_run_id(input_run_id: str, run_id: str | None) -> str:
    if run_id:
        return run_id
    return datetime.now(timezone.utc).strftime(f"{input_run_id}-corpus-gate-%Y%m%d-%H%M%S")


def _parent_run_dir(data_root: str | Path, input_run_id: str) -> Path:
    return Path(data_root) / "runs" / input_run_id


def _stage_run_dir(data_root: str | Path, gate_run_id: str) -> Path:
    return Path(data_root) / "runs" / gate_run_id / STAGE_NAME


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _primary_source_metadata(work_envelope: dict[str, Any]) -> dict[str, Any]:
    raw = work_envelope.get("raw") or {}
    primary_location = raw.get("primary_location") or {}
    source = primary_location.get("source") or {}
    return {
        "openalex_source_id": source.get("id"),
        "openalex_source_display_name": source.get("display_name") or primary_location.get("raw_source_name"),
        "matched_location_ref": "primary_location" if source.get("id") else None,
    }


def _venue_match_metadata(venue_row: VenueTierRow | None) -> dict[str, Any]:
    if venue_row is None:
        return {
            "matched_venue_id": None,
            "matched_alias_type": None,
            "matched_location_ref": None,
            "normalized_tier": None,
            "venue_row_slug": None,
        }
    return {
        "matched_venue_id": venue_row.canonical_venue_slug,
        "matched_alias_type": "openalex_source_id",
        "matched_location_ref": "primary_location",
        "normalized_tier": venue_row.normalized_tier,
        "venue_row_slug": venue_row.canonical_venue_slug,
    }


def _decide_work(work_envelope: dict[str, Any], venue_rows: dict[str, VenueTierRow]) -> tuple[str, list[str], VenueTierRow | None]:
    raw = work_envelope.get("raw") or {}
    if raw.get("is_retracted"):
        return "excluded", ["excluded_retracted"], None
    if raw.get("is_paratext"):
        return "excluded", ["excluded_paratext"], None

    source_details = _primary_source_metadata(work_envelope)
    source_id = source_details["openalex_source_id"]
    if not source_id:
        return "excluded", [missing_primary_source], None

    venue_row = venue_rows.get(source_id)
    if venue_row is None:
        return "excluded", [source_not_in_ai_cs_table], None
    if venue_row.normalized_tier == "UNRESOLVED":
        return "excluded", [venue_row_unresolved], venue_row
    if not venue_row.include_in_ai_cs_corpus:
        return "excluded", [venue_explicitly_excluded], venue_row

    return "include", [matched_ai_cs_venue_tier], venue_row


def _build_included_record(
    work_envelope: dict[str, Any],
    *,
    gate_run_id: str,
    parent_run_id: str,
    venue_row: Any,
    venue_table_hash: str,
) -> dict[str, Any]:
    record = dict(work_envelope)
    record["gate_run_id"] = gate_run_id
    record["parent_run_id"] = parent_run_id
    record["venue_row_slug"] = venue_row.canonical_venue_slug
    record["normalized_tier"] = venue_row.normalized_tier
    record["corpus_gate"] = {
        "decision": "include",
        "reason_code": matched_ai_cs_venue_tier,
        "matched_source_id": venue_row.openalex_source_id,
        "venue_row_slug": venue_row.canonical_venue_slug,
        "normalized_tier": venue_row.normalized_tier,
        "venue_asset_fingerprint": venue_table_hash,
    }
    return record


def _build_decision_record(
    work_envelope: dict[str, Any],
    *,
    gate_run_id: str,
    parent_run_id: str,
    reason_codes: list[str],
    decision: str,
    venue_table_hash: str,
    venue_row: VenueTierRow | None,
) -> dict[str, Any]:
    raw = work_envelope.get("raw") or {}
    source_metadata = _primary_source_metadata(work_envelope)
    match_metadata = _venue_match_metadata(venue_row)
    return {
        "gate_run_id": gate_run_id,
        "parent_run_id": parent_run_id,
        "source_record_id": work_envelope.get("source_record_id"),
        "openalex_work_id": raw.get("id") or work_envelope.get("source_record_id"),
        "openalex_source_id": source_metadata["openalex_source_id"],
        "openalex_source_display_name": source_metadata["openalex_source_display_name"],
        "title": raw.get("display_name") or raw.get("title"),
        "publication_date": raw.get("publication_date"),
        "decision": decision,
        "reason_codes": reason_codes,
        "venue_table_hash": venue_table_hash,
        "matched_venue_id": match_metadata["matched_venue_id"],
        "matched_alias_type": match_metadata["matched_alias_type"],
        "matched_location_ref": match_metadata["matched_location_ref"],
        "normalized_tier": match_metadata["normalized_tier"],
        "venue_row_slug": match_metadata["venue_row_slug"],
    }


def run_corpus_gate(
    *,
    data_root: str | Path,
    input_run_id: str,
    venue_table: str | Path = DEFAULT_VENUE_TIER_ASSET,
    run_id: str | None = None,
) -> dict[str, Any]:
    data_root = Path(data_root)
    parent_run_dir = _parent_run_dir(data_root, input_run_id)
    parent_manifest_path = parent_run_dir / "run.json"
    works_path = parent_run_dir / "openalex" / "works_raw.jsonl"
    if not parent_manifest_path.exists() or not works_path.exists():
        raise SystemExit(f"Missing staged OpenAlex run: {input_run_id}")

    venue_table_path = Path(venue_table)
    venue_rows = load_venue_tiers(venue_table_path)
    venue_table_hash = hash_venue_tier_asset(venue_table_path)

    gate_run_id = _resolve_run_id(input_run_id, run_id)
    stage_run_dir = _stage_run_dir(data_root, gate_run_id)
    if stage_run_dir.exists() and any(stage_run_dir.iterdir()):
        raise SystemExit(f"Gate run already exists: {gate_run_id}")
    stage_run_dir.mkdir(parents=True, exist_ok=True)

    output_path = stage_run_dir / GATED_WORKS_FILENAME
    decisions_path = stage_run_dir / GATE_DECISIONS_FILENAME
    manifest_path = stage_run_dir / "run.json"

    manifest = build_derived_run_manifest(
        stage_name=STAGE_NAME,
        run_id=gate_run_id,
        parent_run_id=input_run_id,
        input_paths={"works_raw.jsonl": str(works_path)},
        output_paths={
            GATED_WORKS_FILENAME: str(output_path),
            GATE_DECISIONS_FILENAME: str(decisions_path),
        },
        asset_fingerprints={venue_table_path.name: venue_table_hash},
        included_count=0,
        excluded_count=0,
    )
    write_derived_run_manifest(manifest, manifest_path)

    work_records = _load_jsonl(works_path)
    included_records: list[dict[str, Any]] = []
    decision_records: list[dict[str, Any]] = []
    included_count = 0
    excluded_count = 0

    for work_envelope in work_records:
        decision, reason_codes, venue_row = _decide_work(work_envelope, venue_rows)
        decision_records.append(
            _build_decision_record(
                work_envelope,
                gate_run_id=gate_run_id,
                parent_run_id=input_run_id,
                reason_codes=reason_codes,
                decision=decision,
                venue_table_hash=venue_table_hash,
                venue_row=venue_row,
            )
        )
        if decision == "include" and venue_row is not None:
            included_record = _build_included_record(
                work_envelope,
                gate_run_id=gate_run_id,
                parent_run_id=input_run_id,
                venue_row=venue_row,
                venue_table_hash=venue_table_hash,
            )
            included_records.append(included_record)
            included_count += 1
        else:
            excluded_count += 1

    if included_records:
        stage_records(output_path, included_records)
    else:
        output_path.touch(exist_ok=True)
    if decision_records:
        stage_records(decisions_path, decision_records)
    else:
        decisions_path.touch(exist_ok=True)

    manifest.included_count = included_count
    manifest.excluded_count = excluded_count
    manifest.completed_at = _utc_now()
    manifest.status = "completed"
    write_derived_run_manifest(manifest, manifest_path)

    return {
        "gate_run_id": gate_run_id,
        "parent_run_id": input_run_id,
        "manifest_path": manifest_path,
        "output_path": output_path,
        "decision_path": decisions_path,
        "included_count": included_count,
        "excluded_count": excluded_count,
        "venue_table_hash": venue_table_hash,
    }
