from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator
import hashlib
import json
import re


SOURCE_RECORD_SCHEMA_VERSION = "sourcing_source_record.v1"
DEFAULT_DOMAIN = "researcher"
SOURCING_STAGE = "sourcing"
SOURCE_RECORDS_FILENAME = "source_records.jsonl"

_SAFE_ID_RE = re.compile(r"[^a-zA-Z0-9_.-]+")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def content_hash(payload: Any) -> str:
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def short_content_hash(payload: Any, *, length: int = 16) -> str:
    return content_hash(payload).split(":", 1)[1][:length]


def safe_id(value: Any, *, fallback: str = "unknown") -> str:
    raw = str(value or "").strip()
    if not raw:
        raw = fallback
    slug = _SAFE_ID_RE.sub("_", raw).strip("._-").lower()
    return slug or fallback


def _last_url_segment(value: str) -> str:
    return value.rstrip("/").rsplit("/", 1)[-1]


def source_native_id(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if "openalex.org/" in text:
        return _last_url_segment(text)
    if "orcid.org/" in text:
        return _last_url_segment(text)
    if "dblp.org/pid/" in text:
        return text.split("/pid/", 1)[1].strip("/")
    return text


def build_source_record_id(*, source: str, entity_type: str, native_id: str, raw_payload: Any | None = None) -> str:
    normalized_native = source_native_id(native_id)
    if not normalized_native and raw_payload is not None:
        normalized_native = short_content_hash(raw_payload)
    if not normalized_native:
        normalized_native = "unknown"
    return f"src_{safe_id(source)}_{safe_id(entity_type)}_{safe_id(normalized_native)}"


def raw_storage_path(*, domain: str, source: str, run_id: str, source_record_id: str) -> str:
    return f"sourcing/raw/{safe_id(domain)}/{safe_id(source)}/{safe_id(run_id)}/{safe_id(source_record_id)}.json"


def load_jsonl(path: Path | str) -> list[dict[str, Any]]:
    target = Path(path)
    return [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path | str, records: Iterable[dict[str, Any]]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return target


def sourcing_dir(data_root: Path | str, run_id: str) -> Path:
    return Path(data_root) / "runs" / run_id / SOURCING_STAGE


def default_source_records_path(data_root: Path | str, run_id: str) -> Path:
    return sourcing_dir(data_root, run_id) / SOURCE_RECORDS_FILENAME


@dataclass(frozen=True)
class StagedJsonlRecord:
    path: Path
    record: dict[str, Any]


def iter_staged_jsonl(data_root: Path | str, run_id: str) -> Iterator[StagedJsonlRecord]:
    run_dir = Path(data_root) / "runs" / run_id
    if not run_dir.exists():
        raise SystemExit(f"Missing input run: {run_id}")
    for path in sorted(run_dir.rglob("*.jsonl")):
        relative_parts = path.relative_to(run_dir).parts
        if relative_parts and relative_parts[0] == SOURCING_STAGE:
            continue
        for record in load_jsonl(path):
            yield StagedJsonlRecord(path=path, record=record)


def _path_source(path: Path) -> str:
    parts = path.parts
    if len(parts) >= 2:
        return parts[-2]
    return "generic"


def _envelope_source(record: dict[str, Any], path: Path) -> str:
    source = record.get("source")
    if isinstance(source, str) and source:
        return source
    if _is_contact_enrichment(record):
        return "contact_enrichment"
    return _path_source(path)


def _envelope_entity_type(record: dict[str, Any]) -> str:
    raw_type = str(record.get("entity_type") or record.get("entityType") or "").lower()
    if raw_type in {"authors", "author", "person", "people"}:
        return "person_profile"
    if raw_type in {"works", "work", "paper", "papers", "research_work"}:
        return "research_work"
    if _is_contact_enrichment(record):
        return "person_profile"
    return safe_id(raw_type or "generic_record")


def _is_contact_enrichment(record: dict[str, Any]) -> bool:
    return any(key in record for key in ("openalex_author_id", "emails", "homepages", "profile_urls", "openreview", "dblp"))


def _raw_payload(record: dict[str, Any]) -> dict[str, Any]:
    raw = record.get("raw")
    return raw if isinstance(raw, dict) else record


def _first_non_empty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def _openalex_work_display(raw: dict[str, Any]) -> dict[str, Any]:
    primary_location = raw.get("primary_location") or {}
    source = primary_location.get("source") or {}
    return {
        "title": _first_non_empty(raw.get("display_name"), raw.get("title")),
        "venue": _first_non_empty(source.get("display_name"), primary_location.get("raw_source_name")),
        "publicationDate": raw.get("publication_date"),
    }


def _openalex_work_summary(raw: dict[str, Any]) -> dict[str, Any]:
    primary_location = raw.get("primary_location") or {}
    source = primary_location.get("source") or {}
    return _compact_dict(
        {
            "doi": raw.get("doi"),
            "citedByCount": raw.get("cited_by_count"),
            "publicationDate": raw.get("publication_date"),
            "publicationYear": raw.get("publication_year"),
            "venue": _first_non_empty(source.get("display_name"), primary_location.get("raw_source_name")),
            "venueOpenAlexId": source.get("id"),
            "authorsCount": len(raw.get("authorships") or []),
        }
    )


def _person_display(raw: dict[str, Any]) -> dict[str, Any]:
    return _compact_dict(
        {
            "name": _first_non_empty(raw.get("name"), raw.get("display_name"), raw.get("fullName")),
            "institution": _first_non_empty(raw.get("institution"), raw.get("last_known_institution")),
        }
    )


def _person_summary(raw: dict[str, Any]) -> dict[str, Any]:
    emails = raw.get("emails") if isinstance(raw.get("emails"), list) else []
    homepages = raw.get("homepages") if isinstance(raw.get("homepages"), list) else []
    openreview = raw.get("openreview") if isinstance(raw.get("openreview"), dict) else {}
    dblp = raw.get("dblp") if isinstance(raw.get("dblp"), dict) else {}
    return _compact_dict(
        {
            "orcid": raw.get("orcid"),
            "institution": raw.get("institution"),
            "institutionCountry": raw.get("institution_country"),
            "institutionRor": raw.get("institution_ror"),
            "isCorresponding": raw.get("is_corresponding"),
            "paperCountInBatch": raw.get("paper_count_in_batch"),
            "emailCount": len(emails),
            "homepageCount": len(homepages),
            "openreviewId": openreview.get("openreview_id"),
            "dblpPid": dblp.get("dblp_pid"),
        }
    )


def _generic_display(raw: dict[str, Any]) -> dict[str, Any]:
    return _compact_dict(
        {
            "name": _first_non_empty(raw.get("name"), raw.get("display_name"), raw.get("fullName")),
            "title": _first_non_empty(raw.get("title"), raw.get("display_name")),
        }
    )


def _generic_summary(raw: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for key in ("id", "source_record_id", "doi", "orcid", "homepage", "url"):
        if key in raw:
            summary[key] = raw[key]
    return _compact_dict(summary)


def _compact_dict(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


def _native_id(record: dict[str, Any], raw: dict[str, Any], entity_type: str) -> str:
    if _is_contact_enrichment(record):
        return str(_first_non_empty(record.get("openalex_author_id"), raw.get("orcid"), raw.get("name"), record.get("name")) or "")
    return str(
        _first_non_empty(
            record.get("source_record_id"),
            record.get("sourceRecordId"),
            raw.get("id"),
            raw.get("source_record_id"),
            raw.get("doi"),
            raw.get("orcid"),
            raw.get("url"),
            short_content_hash(record) if entity_type == "generic_record" else None,
        )
        or ""
    )


def _timestamps(record: dict[str, Any], fallback_timestamp: str | None = None) -> tuple[str, str]:
    observed = _first_non_empty(
        record.get("fetched_at"),
        record.get("updated_at"),
        record.get("updatedAt"),
        record.get("created_at"),
        record.get("createdAt"),
        fallback_timestamp,
    )
    timestamp = str(observed or utc_now())
    return timestamp, timestamp


def to_source_record(
    staged: StagedJsonlRecord,
    *,
    run_id: str,
    domain: str = DEFAULT_DOMAIN,
    fallback_timestamp: str | None = None,
) -> dict[str, Any]:
    record = staged.record
    raw = _raw_payload(record)
    source = _envelope_source(record, staged.path)
    entity_type = _envelope_entity_type(record)
    native_id = source_native_id(_native_id(record, raw, entity_type))
    source_record_id = build_source_record_id(
        source=source,
        entity_type=entity_type,
        native_id=native_id,
        raw_payload=record,
    )

    if source == "openalex" and entity_type == "research_work":
        display = _openalex_work_display(raw)
        raw_summary = _openalex_work_summary(raw)
    elif entity_type == "person_profile":
        display = _person_display(raw)
        raw_summary = _person_summary(raw)
    else:
        display = _generic_display(raw)
        raw_summary = _generic_summary(raw)

    created_at, updated_at = _timestamps(record, fallback_timestamp)
    return {
        "sourceRecordId": source_record_id,
        "runId": run_id,
        "domain": domain,
        "source": source,
        "entityType": entity_type,
        "sourceNativeId": native_id or source_record_id,
        "display": display,
        "rawSummary": raw_summary,
        "rawStoragePath": raw_storage_path(
            domain=domain,
            source=source,
            run_id=run_id,
            source_record_id=source_record_id,
        ),
        "contentHash": content_hash(record),
        "schemaVersion": SOURCE_RECORD_SCHEMA_VERSION,
        "createdAt": created_at,
        "updatedAt": updated_at,
    }


def collect_source_records(
    *,
    data_root: Path | str,
    run_id: str,
    domain: str = DEFAULT_DOMAIN,
    fallback_timestamp: str | None = None,
) -> list[dict[str, Any]]:
    return [
        to_source_record(staged, run_id=run_id, domain=domain, fallback_timestamp=fallback_timestamp)
        for staged in iter_staged_jsonl(data_root, run_id)
    ]

