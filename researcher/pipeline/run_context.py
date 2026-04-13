from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json
import shutil

from config.source_registry import SOURCE_REGISTRY, validate_source_selection


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fingerprint(parts: list[str]) -> str:
    digest = hashlib.sha256()
    digest.update("\n".join(parts).encode("utf-8"))
    return digest.hexdigest()[:16]


@dataclass(frozen=True)
class SourceAttempt:
    request_params: dict[str, Any]
    retry_count: int
    checkpoint_cursor: str | None
    page_count: int
    record_count: int
    error_summary: str


@dataclass
class RunManifest:
    run_id: str
    source_name: str
    slice_type: str
    slice_value: str
    since_year: int
    query_hash: str
    max_records: int
    max_pages: int | None
    default_retry_limit: int
    sources_requested: tuple[str, ...]
    config_fingerprint: str | None = None
    parent_run_id: str | None = None
    created_at: str = field(default_factory=_utc_now)
    completed_at: str | None = None
    status: str = "running"
    sources_completed: list[str] = field(default_factory=list)
    source_attempts: dict[str, SourceAttempt] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "source_name": self.source_name,
            "slice": {
                "type": self.slice_type,
                "value": self.slice_value,
            },
            "since_year": self.since_year,
            "query_hash": self.query_hash,
            "limits": {
                "max_records": self.max_records,
                "max_pages": self.max_pages,
            },
            "retries": {
                "default_retry_limit": self.default_retry_limit,
            },
            "sources_requested": list(self.sources_requested),
            "sources_completed": list(self.sources_completed),
            "config_fingerprint": self.config_fingerprint,
            "parent_run_id": self.parent_run_id,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "source_attempts": {
                source_id: asdict(attempt) for source_id, attempt in self.source_attempts.items()
            },
        }


@dataclass
class RunContext:
    data_root: Path
    manifest: RunManifest

    def __post_init__(self) -> None:
        self.data_root = Path(self.data_root)
        self.manifest.sources_requested = validate_source_selection(self.manifest.sources_requested)
        self._ensure_layout()

    @property
    def run_id(self) -> str:
        return self.manifest.run_id

    @property
    def run_dir(self) -> Path:
        return self.data_root / "runs" / self.run_id

    @property
    def latest_dir(self) -> Path:
        return self.data_root / "latest"

    @property
    def manifest_path(self) -> Path:
        return self.run_dir / "run.json"

    @property
    def latest_manifest_path(self) -> Path:
        return self.latest_dir / "run.json"

    def _ensure_layout(self) -> None:
        for path in (
            self.run_dir,
            self.run_dir / "checkpoints",
            self.latest_dir,
            self.latest_dir / "checkpoints",
        ):
            path.mkdir(parents=True, exist_ok=True)
        for source_id in SOURCE_REGISTRY:
            self.source_dir(source_id).mkdir(parents=True, exist_ok=True)
            self.latest_source_dir(source_id).mkdir(parents=True, exist_ok=True)

    def source_dir(self, source_id: str) -> Path:
        return self.run_dir / source_id

    def latest_source_dir(self, source_id: str) -> Path:
        return self.latest_dir / source_id

    def raw_path(self, source_id: str, filename: str) -> Path:
        return self.source_dir(source_id) / filename

    def latest_raw_path(self, source_id: str, filename: str) -> Path:
        return self.latest_source_dir(source_id) / filename

    def checkpoint_path(self, source_id: str) -> Path:
        return self.run_dir / "checkpoints" / f"{source_id}.json"

    def latest_checkpoint_path(self, source_id: str) -> Path:
        return self.latest_dir / "checkpoints" / f"{source_id}.json"

    def initialize(self) -> dict[str, Any]:
        manifest = self.manifest.to_dict()
        write_run_manifest(self.manifest, self.manifest_path, latest_path=self.latest_manifest_path)
        return manifest

    def write_manifest(self, *, status: str | None = None, completed_at: str | None = None) -> dict[str, Any]:
        if status is not None:
            self.manifest.status = status
        if completed_at is not None:
            self.manifest.completed_at = completed_at
        elif self.manifest.status == "completed" and self.manifest.completed_at is None:
            self.manifest.completed_at = _utc_now()

        manifest = self.manifest.to_dict()
        write_run_manifest(self.manifest, self.manifest_path, latest_path=self.latest_manifest_path)
        return manifest

    def record_source_attempt(self, source_id: str, attempt: SourceAttempt) -> None:
        if source_id not in SOURCE_REGISTRY:
            raise ValueError(f"Unknown source: {source_id}")
        self.manifest.source_attempts[source_id] = attempt
        _json_dump(self.checkpoint_path(source_id), asdict(attempt))
        shutil.copyfile(self.checkpoint_path(source_id), self.latest_checkpoint_path(source_id))

    def complete_source(self, source_id: str) -> None:
        if source_id not in self.manifest.sources_completed:
            self.manifest.sources_completed.append(source_id)


def build_run_manifest(
    *,
    run_id: str,
    source_name: str,
    slice_type: str,
    slice_value: str,
    since_year: int,
    max_records: int,
    max_pages: int | None,
    default_retry_limit: int,
    sources_requested: tuple[str, ...] | list[str] | None,
    config_fingerprint: str | None = None,
    parent_run_id: str | None = None,
) -> RunManifest:
    requested = validate_source_selection(sources_requested)
    query_hash = _fingerprint(
        [
            source_name,
            slice_type,
            slice_value,
            str(since_year),
            str(max_records),
            str(max_pages),
            str(default_retry_limit),
            ",".join(requested),
            parent_run_id or "",
        ]
    )
    return RunManifest(
        run_id=run_id,
        source_name=source_name,
        slice_type=slice_type,
        slice_value=slice_value,
        since_year=since_year,
        query_hash=query_hash,
        max_records=max_records,
        max_pages=max_pages,
        default_retry_limit=default_retry_limit,
        sources_requested=requested,
        config_fingerprint=config_fingerprint,
        parent_run_id=parent_run_id,
    )


def write_run_manifest(
    manifest: RunManifest,
    path: Path | str,
    *,
    latest_path: Path | str | None = None,
) -> Path:
    target = Path(path)
    _json_dump(target, manifest.to_dict())
    if latest_path is not None:
        latest_target = Path(latest_path)
        latest_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, latest_target)
    return target


def create_run_context(
    *,
    data_root: Path | str,
    run_id: str,
    preset_type: str,
    preset_value: str,
    since_year: int,
    max_records: int,
    max_pages: int | None = None,
    default_retry_limit: int = 3,
    source_name: str | None = None,
    sources_requested: tuple[str, ...] | list[str] | None,
    config_fingerprint: str | None = None,
    parent_run_id: str | None = None,
) -> RunContext:
    requested = validate_source_selection(sources_requested)
    manifest = build_run_manifest(
        run_id=run_id,
        source_name=source_name or requested[0],
        slice_type=preset_type,
        slice_value=preset_value,
        since_year=since_year,
        max_records=max_records,
        max_pages=max_pages,
        default_retry_limit=default_retry_limit,
        sources_requested=requested,
        config_fingerprint=config_fingerprint,
        parent_run_id=parent_run_id,
    )
    return RunContext(
        data_root=Path(data_root),
        manifest=manifest,
    )
