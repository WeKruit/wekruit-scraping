from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import csv


CSV_COLUMNS = (
    "canonical_venue_slug",
    "canonical_venue_name",
    "venue_kind",
    "openalex_source_id",
    "openalex_source_display_name",
    "ccf_grade",
    "core_grade",
    "normalized_tier",
    "include_in_ai_cs_corpus",
    "evidence_ccf_url",
    "evidence_core_url",
    "last_reviewed_at",
    "review_notes",
)

ALLOWED_NORMALIZED_TIERS = {"T1", "T2", "T3", "T4", "EXCLUDE", "UNRESOLVED"}
RANKING_TIERS = {"T1", "T2", "T3", "T4"}

matched_ai_cs_venue_tier = "matched_ai_cs_venue_tier"
missing_primary_source = "missing_primary_source"
source_not_in_ai_cs_table = "source_not_in_ai_cs_table"
venue_row_unresolved = "venue_row_unresolved"
venue_explicitly_excluded = "venue_explicitly_excluded"

DEFAULT_VENUE_TIER_ASSET = Path(__file__).resolve().parents[1] / "data" / "assets" / "ai_cs_venue_tiers.csv"


@dataclass(frozen=True, slots=True)
class VenueTierRow:
    canonical_venue_slug: str
    canonical_venue_name: str
    venue_kind: str
    openalex_source_id: str
    openalex_source_display_name: str
    ccf_grade: str
    core_grade: str
    normalized_tier: str
    include_in_ai_cs_corpus: bool
    evidence_ccf_url: str
    evidence_core_url: str
    last_reviewed_at: str
    review_notes: str


def hash_venue_tier_asset(path: str | Path = DEFAULT_VENUE_TIER_ASSET) -> str:
    return sha256(Path(path).read_bytes()).hexdigest()


def load_venue_tiers(path: str | Path = DEFAULT_VENUE_TIER_ASSET) -> dict[str, VenueTierRow]:
    asset_path = Path(path)
    with asset_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(CSV_COLUMNS):
            raise ValueError(f"Unexpected venue tier CSV header: {reader.fieldnames!r}")

        rows: dict[str, VenueTierRow] = {}
        for line_number, raw_row in enumerate(reader, start=2):
            row = {key: (value or "").strip() for key, value in raw_row.items()}
            _validate_row(row, line_number=line_number)
            source_id = row["openalex_source_id"]
            if source_id in rows:
                raise ValueError(f"Duplicate openalex_source_id at line {line_number}: {source_id}")

            rows[source_id] = VenueTierRow(
                canonical_venue_slug=row["canonical_venue_slug"],
                canonical_venue_name=row["canonical_venue_name"],
                venue_kind=row["venue_kind"],
                openalex_source_id=source_id,
                openalex_source_display_name=row["openalex_source_display_name"],
                ccf_grade=row["ccf_grade"],
                core_grade=row["core_grade"],
                normalized_tier=row["normalized_tier"],
                include_in_ai_cs_corpus=_parse_bool(row["include_in_ai_cs_corpus"], line_number),
                evidence_ccf_url=row["evidence_ccf_url"],
                evidence_core_url=row["evidence_core_url"],
                last_reviewed_at=row["last_reviewed_at"],
                review_notes=row["review_notes"],
            )
        return rows


def _validate_row(row: dict[str, str], *, line_number: int) -> None:
    required_fields = (
        "canonical_venue_slug",
        "canonical_venue_name",
        "venue_kind",
        "openalex_source_id",
        "openalex_source_display_name",
        "normalized_tier",
        "include_in_ai_cs_corpus",
        "last_reviewed_at",
        "review_notes",
    )
    for field in required_fields:
        if not row.get(field):
            raise ValueError(f"Blank required field {field!r} at line {line_number}")

    normalized_tier = row["normalized_tier"]
    if normalized_tier not in ALLOWED_NORMALIZED_TIERS:
        raise ValueError(f"Invalid normalized_tier {normalized_tier!r} at line {line_number}")

    include = _parse_bool(row["include_in_ai_cs_corpus"], line_number)
    if normalized_tier in RANKING_TIERS and not include:
        raise ValueError(f"Tier {normalized_tier} must be included at line {line_number}")
    if normalized_tier in {"EXCLUDE", "UNRESOLVED"} and include:
        raise ValueError(f"Tier {normalized_tier} must be excluded at line {line_number}")

    _parse_iso8601(row["last_reviewed_at"], line_number)


def _parse_bool(value: str, line_number: int) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError(f"Invalid include_in_ai_cs_corpus value {value!r} at line {line_number}")


def _parse_iso8601(value: str, line_number: int) -> datetime:
    candidate = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"Invalid last_reviewed_at {value!r} at line {line_number}") from exc
