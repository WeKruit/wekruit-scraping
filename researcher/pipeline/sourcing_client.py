from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

import requests

from pipeline.sourcing_records import content_hash, default_source_records_path, utc_now, write_jsonl


DEFAULT_BATCH_SIZE = 100


@dataclass(frozen=True)
class UploadResult:
    dry_run: bool
    run_payload_path: Path | None
    records_payload_path: Path | None
    summary_path: Path | None
    record_count: int
    source_count: int


def build_source_run_payload(
    *,
    run_id: str,
    domain: str,
    records: list[dict[str, Any]],
    trigger: str = "local_worker",
    timestamp: str | None = None,
) -> dict[str, Any]:
    now = timestamp or utc_now()
    sources = sorted({str(record["source"]) for record in records})
    return {
        "runId": run_id,
        "domain": domain,
        "source": sources[0] if len(sources) == 1 else "mixed",
        "sources": sources,
        "trigger": trigger,
        "status": "running",
        "startedAt": now,
        "completedAt": None,
        "schemaVersion": "sourcing_source_run.v1",
        "contentHash": content_hash({"runId": run_id, "domain": domain, "sources": sources, "records": len(records)}),
        "counts": {
            "received": len(records),
            "stored": 0,
            "skipped": 0,
            "failed": 0,
            "contentHashDuplicates": 0,
        },
    }


def build_complete_source_run_payload(
    *,
    status: str = "completed",
    record_count: int,
    timestamp: str | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "completedAt": timestamp or utc_now(),
        "counts": {
            "received": record_count,
        },
    }


class SourcingIngestClient:
    def __init__(self, *, api_base_url: str, timeout_seconds: int = 30) -> None:
        self.api_base_url = api_base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def create_source_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/source-runs", payload)

    def batch_upsert_source_records(self, *, run_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
        return self._post("/source-records:batchUpsert", {"runId": run_id, "records": records})

    def complete_source_run(self, *, run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post(f"/source-runs/{run_id}/complete", payload)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(f"{self.api_base_url}{path}", json=payload, timeout=self.timeout_seconds)
        response.raise_for_status()
        if not response.content:
            return {}
        return response.json()


def dry_run_upload(
    *,
    data_root: Path | str,
    run_id: str,
    domain: str,
    records: list[dict[str, Any]],
) -> UploadResult:
    output_path = default_source_records_path(data_root, run_id)
    run_payload_path = output_path.parent / "source_run.json"
    summary_path = output_path.parent / "upload_summary.json"
    source_run_payload = build_source_run_payload(run_id=run_id, domain=domain, records=records)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_payload_path.write_text(json.dumps(source_run_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_jsonl(output_path, records)
    summary = {
        "dryRun": True,
        "runId": run_id,
        "domain": domain,
        "recordCount": len(records),
        "sourceCount": len(source_run_payload["sources"]),
        "sourceRunPath": str(run_payload_path),
        "sourceRecordsPath": str(output_path),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return UploadResult(
        dry_run=True,
        run_payload_path=run_payload_path,
        records_payload_path=output_path,
        summary_path=summary_path,
        record_count=len(records),
        source_count=len(source_run_payload["sources"]),
    )


def upload_source_records(
    *,
    api_base_url: str,
    run_id: str,
    domain: str,
    records: list[dict[str, Any]],
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> UploadResult:
    client = SourcingIngestClient(api_base_url=api_base_url)
    client.create_source_run(build_source_run_payload(run_id=run_id, domain=domain, records=records))
    for start in range(0, len(records), batch_size):
        batch = records[start : start + batch_size]
        client.batch_upsert_source_records(run_id=run_id, records=batch)
    client.complete_source_run(
        run_id=run_id,
        payload=build_complete_source_run_payload(record_count=len(records)),
    )
    return UploadResult(
        dry_run=False,
        run_payload_path=None,
        records_payload_path=None,
        summary_path=None,
        record_count=len(records),
        source_count=len({str(record["source"]) for record in records}),
    )

