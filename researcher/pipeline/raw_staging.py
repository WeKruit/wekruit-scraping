from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
import json


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_raw_envelope(
    *,
    run_id: str,
    source_id: str,
    entity_type: str,
    source_record_id: str,
    slice_definition: dict[str, Any],
    checkpoint_cursor: str | None,
    raw: dict[str, Any],
    page_number: int | None = None,
    retry_count: int = 0,
    error_summary: str = "",
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "source": source_id,
        "entity_type": entity_type,
        "source_record_id": source_record_id,
        "slice": slice_definition,
        "fetched_at": _utc_now(),
        "checkpoint_cursor": checkpoint_cursor,
        "page_number": page_number,
        "retry_count": retry_count,
        "error_summary": error_summary,
        "raw": raw,
    }


def stage_records(path: Path | str, records: Iterable[dict[str, Any]], *, mirror_path: Path | str | None = None) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    mirror_target = Path(mirror_path) if mirror_path is not None else None
    if mirror_target is not None:
        mirror_target.parent.mkdir(parents=True, exist_ok=True)

    lines = [json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records]
    if lines:
        with target.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        if mirror_target is not None:
            with mirror_target.open("a", encoding="utf-8") as handle:
                handle.write("\n".join(lines) + "\n")
    elif mirror_target is not None and not mirror_target.exists():
        mirror_target.touch()
    return target


def stage_record(path: Path | str, record: dict[str, Any], *, mirror_path: Path | str | None = None) -> Path:
    return stage_records(path, [record], mirror_path=mirror_path)
