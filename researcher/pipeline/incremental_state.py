from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import json


def _state_root(data_root: Path | str) -> Path:
    return Path(data_root) / "state"


def _source_state_dir(data_root: Path | str, source_id: str) -> Path:
    return _state_root(data_root) / source_id


def checkpoint_path(data_root: Path | str, *, lineage_key: str, source_id: str) -> Path:
    return _source_state_dir(data_root, source_id) / f"{lineage_key}-checkpoint.json"


def read_checkpoint(data_root: Path | str, *, lineage_key: str, source_id: str) -> dict[str, Any]:
    path = checkpoint_path(data_root, lineage_key=lineage_key, source_id=source_id)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_checkpoint(
    data_root: Path | str,
    *,
    lineage_key: str,
    source_id: str,
    payload: dict[str, Any],
) -> Path:
    path = checkpoint_path(data_root, lineage_key=lineage_key, source_id=source_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def seen_ids_path(data_root: Path | str, *, lineage_key: str, source_id: str) -> Path:
    return _source_state_dir(data_root, source_id) / f"{lineage_key}-seen.json"


def load_seen_ids(data_root: Path | str, *, lineage_key: str, source_id: str) -> set[str]:
    path = seen_ids_path(data_root, lineage_key=lineage_key, source_id=source_id)
    if not path.exists():
        return set()
    return set(json.loads(path.read_text(encoding="utf-8")))


def write_seen_ids(
    data_root: Path | str,
    *,
    lineage_key: str,
    source_id: str,
    values: Iterable[str],
) -> Path:
    path = seen_ids_path(data_root, lineage_key=lineage_key, source_id=source_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted({value for value in values if value})
    path.write_text(json.dumps(ordered, indent=2) + "\n", encoding="utf-8")
    return path
