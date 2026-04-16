import json
from pathlib import Path

from pipeline.raw_staging import stage_records
from pipeline.run_context import create_run_context
from pipeline.sourcing_client import upload_source_records
from pipeline.sourcing_records import collect_source_records, content_hash
from scripts import s3_upload_source_records
from sources.openalex import OpenAlexAdapter


ROOT = Path(__file__).resolve().parents[1]
OPENALEX_WORKS_FIXTURE = ROOT / "tests" / "fixtures" / "openalex" / "works_page.json"


def _load_openalex_records(run_id: str) -> tuple[list[dict], list[dict]]:
    page = json.loads(OPENALEX_WORKS_FIXTURE.read_text(encoding="utf-8"))
    preset = {
        "family": "venue",
        "label": "Neural Information Processing Systems",
    }
    return OpenAlexAdapter().parse_page(
        page["results"],
        preset=preset,
        run_id=run_id,
        page_number=1,
        checkpoint_cursor="*",
    )


def _stage_run(tmp_path: Path, run_id: str = "input-run-1") -> Path:
    ctx = create_run_context(
        data_root=tmp_path / "data",
        run_id=run_id,
        preset_type="venue",
        preset_value="NeurIPS",
        since_year=2024,
        max_records=10,
        max_pages=1,
        default_retry_limit=3,
        sources_requested=("openalex",),
        config_fingerprint="fingerprint-sourcing",
    )
    ctx.initialize()
    works, authors = _load_openalex_records(run_id)
    stage_records(ctx.raw_path("openalex", "works_raw.jsonl"), works)
    stage_records(ctx.raw_path("openalex", "authors_raw.jsonl"), authors)
    return tmp_path / "data"


def test_source_record_adapter_is_deterministic_and_hashes_raw_envelopes(tmp_path):
    data_root = _stage_run(tmp_path)

    first = collect_source_records(data_root=data_root, run_id="input-run-1")
    second = collect_source_records(data_root=data_root, run_id="input-run-1")

    assert first == second
    assert len(first) == 4

    authors = [record for record in first if record["entityType"] == "person_profile"]
    works = [record for record in first if record["entityType"] == "research_work"]
    assert [record["sourceRecordId"] for record in authors] == [
        "src_openalex_person_profile_a1",
        "src_openalex_person_profile_a2",
    ]
    assert [record["sourceRecordId"] for record in works] == [
        "src_openalex_research_work_w1",
        "src_openalex_research_work_w2",
    ]

    author_envelope = json.loads((data_root / "runs" / "input-run-1" / "openalex" / "authors_raw.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert authors[0]["sourceNativeId"] == "A1"
    assert authors[0]["display"] == {"name": "Ada Lovelace", "institution": "Institute of AI"}
    assert authors[0]["rawSummary"]["orcid"] == "0000-0001-1111-1111"
    assert authors[0]["rawStoragePath"] == "sourcing/raw/researcher/openalex/input-run-1/src_openalex_person_profile_a1.json"
    assert authors[0]["contentHash"] == content_hash(author_envelope)

    assert works[0]["display"]["title"] == "Transformer Models for AI"
    assert works[0]["display"]["venue"] == "NeurIPS"
    assert works[0]["rawSummary"]["doi"] == "https://doi.org/10.1000/example1"
    assert works[0]["schemaVersion"] == "sourcing_source_record.v1"


def test_adapter_supports_contact_style_records_and_generic_fallback(tmp_path):
    data_root = _stage_run(tmp_path)
    run_dir = data_root / "runs" / "input-run-1"
    contact_record = {
        "openalex_author_id": "https://openalex.org/A1",
        "name": "Shan Wang",
        "orcid": "0000-0002-0698-4341",
        "institution": "Institute of AI",
        "emails": [{"value": "shan@example.edu", "source": "orcid"}],
        "homepages": [{"value": "https://shan.example.edu", "source": "openreview"}],
        "openreview": {"openreview_id": "~Shan_Wang1"},
        "dblp": {"dblp_pid": "62/3650"},
    }
    generic_record = {"external_id": "manual-1", "title": "Manual upload row", "url": "https://example.edu/manual-1"}
    stage_records(run_dir / "contact_enrichment" / "contacts_raw.jsonl", [contact_record])
    stage_records(run_dir / "manual" / "rows.jsonl", [generic_record])

    records = collect_source_records(data_root=data_root, run_id="input-run-1")
    by_id = {record["sourceRecordId"]: record for record in records}

    contact = by_id["src_contact_enrichment_person_profile_a1"]
    assert contact["source"] == "contact_enrichment"
    assert contact["entityType"] == "person_profile"
    assert contact["rawSummary"]["emailCount"] == 1
    assert contact["rawSummary"]["homepageCount"] == 1
    assert contact["rawSummary"]["openreviewId"] == "~Shan_Wang1"
    assert contact["rawSummary"]["dblpPid"] == "62/3650"

    generic = [record for record in records if record["source"] == "manual"][0]
    assert generic["entityType"] == "generic_record"
    assert generic["display"] == {"title": "Manual upload row"}
    assert generic["rawStoragePath"].startswith("sourcing/raw/researcher/manual/input-run-1/")


def test_upload_cli_dry_run_writes_local_source_record_payload(tmp_path, monkeypatch):
    data_root = _stage_run(tmp_path)

    def fail_network_upload(**kwargs):
        raise AssertionError("dry-run must not attempt network upload")

    monkeypatch.setattr(s3_upload_source_records, "upload_source_records", fail_network_upload)

    exit_code = s3_upload_source_records.main([
        "--input-run",
        "input-run-1",
        "--output-root",
        str(data_root),
        "--dry-run",
    ])

    assert exit_code == 0
    sourcing_dir = data_root / "runs" / "input-run-1" / "sourcing"
    records_path = sourcing_dir / "source_records.jsonl"
    run_path = sourcing_dir / "source_run.json"
    summary_path = sourcing_dir / "upload_summary.json"

    assert records_path.exists()
    assert run_path.exists()
    assert summary_path.exists()

    records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 4
    assert {record["domain"] for record in records} == {"researcher"}
    assert {record["source"] for record in records} == {"openalex"}
    assert records[0]["rawStoragePath"].startswith("sourcing/raw/researcher/openalex/input-run-1/")

    run_payload = json.loads(run_path.read_text(encoding="utf-8"))
    assert run_payload["runId"] == "input-run-1"
    assert run_payload["domain"] == "researcher"
    assert run_payload["source"] == "openalex"
    assert run_payload["sources"] == ["openalex"]
    assert run_payload["counts"]["received"] == 4

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["dryRun"] is True
    assert summary["recordCount"] == 4
    assert summary["sourceCount"] == 1


def test_upload_client_posts_core_service_routes_in_order(monkeypatch):
    calls = []

    class _Response:
        content = b"{}"

        def raise_for_status(self):
            return None

        def json(self):
            return {}

    def fake_post(url, *, json, timeout):
        calls.append({"url": url, "json": json, "timeout": timeout})
        return _Response()

    monkeypatch.setattr("pipeline.sourcing_client.requests.post", fake_post)

    records = [
        {
            "sourceRecordId": "src_openalex_person_profile_a1",
            "runId": "input-run-1",
            "domain": "researcher",
            "source": "openalex",
            "entityType": "person_profile",
            "sourceNativeId": "A1",
            "display": {"name": "Ada Lovelace"},
            "rawSummary": {},
            "rawStoragePath": "sourcing/raw/researcher/openalex/input-run-1/src_openalex_person_profile_a1.json",
            "contentHash": "sha256:test1",
            "schemaVersion": "sourcing_source_record.v1",
            "createdAt": "2026-04-15T00:00:00Z",
            "updatedAt": "2026-04-15T00:00:00Z",
        },
        {
            "sourceRecordId": "src_openalex_person_profile_a2",
            "runId": "input-run-1",
            "domain": "researcher",
            "source": "openalex",
            "entityType": "person_profile",
            "sourceNativeId": "A2",
            "display": {"name": "Grace Hopper"},
            "rawSummary": {},
            "rawStoragePath": "sourcing/raw/researcher/openalex/input-run-1/src_openalex_person_profile_a2.json",
            "contentHash": "sha256:test2",
            "schemaVersion": "sourcing_source_record.v1",
            "createdAt": "2026-04-15T00:00:00Z",
            "updatedAt": "2026-04-15T00:00:00Z",
        },
    ]

    result = upload_source_records(
        api_base_url="http://127.0.0.1:5101/api/sourcing",
        run_id="input-run-1",
        domain="researcher",
        records=records,
        batch_size=1,
    )

    assert result.dry_run is False
    assert result.record_count == 2
    assert [call["url"] for call in calls] == [
        "http://127.0.0.1:5101/api/sourcing/source-runs",
        "http://127.0.0.1:5101/api/sourcing/source-records:batchUpsert",
        "http://127.0.0.1:5101/api/sourcing/source-records:batchUpsert",
        "http://127.0.0.1:5101/api/sourcing/source-runs/input-run-1/complete",
    ]
    assert calls[0]["json"]["runId"] == "input-run-1"
    assert calls[0]["json"]["source"] == "openalex"
    assert calls[1]["json"]["records"] == [records[0]]
    assert calls[2]["json"]["records"] == [records[1]]
    assert calls[3]["json"]["status"] == "completed"
