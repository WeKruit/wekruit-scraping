import ast
import json
from pathlib import Path

import pytest

from config.source_registry import SOURCE_REGISTRY, get_source_config, get_source_registry, validate_source_selection
from pipeline.raw_staging import build_raw_envelope, stage_record, stage_records
from pipeline.run_context import RunContext, RunManifest, SourceAttempt, build_run_manifest, create_run_context


ROOT = Path(__file__).resolve().parents[1]
SETTINGS_EXAMPLE = ROOT / "config" / "settings.example.py"


def _assigned_uppercase_names(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    names.append(target.id)
    return names


def test_settings_example_is_phase1_only():
    namespace: dict[str, object] = {}
    exec(compile(SETTINGS_EXAMPLE.read_text(encoding="utf-8"), str(SETTINGS_EXAMPLE), "exec"), namespace)

    expected_names = {
        "DATA_ROOT",
        "DEFAULT_MAX_RECORDS",
        "DEFAULT_MAX_PAGES",
        "DEFAULT_RETRY_LIMIT",
        "OPENALEX_EMAIL",
        "OPENALEX_API_KEY",
        "OPENALEX_PAGE_SIZE",
        "OPENALEX_BACKOFF_SECONDS",
        "CROSSREF_MAILTO",
        "CROSSREF_PAGE_SIZE",
        "CROSSREF_BACKOFF_SECONDS",
    }

    assert set(_assigned_uppercase_names(SETTINGS_EXAMPLE)) == expected_names
    assert namespace["DATA_ROOT"] == "data"
    assert namespace["OPENALEX_EMAIL"] == "adam@wekruit.com"
    assert namespace["CROSSREF_MAILTO"] == "adam@wekruit.com"
    assert namespace["DEFAULT_MAX_RECORDS"] == 1000
    assert namespace["DEFAULT_MAX_PAGES"] == 5
    assert namespace["DEFAULT_RETRY_LIMIT"] == 3
    assert "S2_API_KEY" not in namespace
    assert "NCBI_API_KEY" not in namespace
    assert "CONTACTOUT_API_KEY" not in namespace
    assert "PDL_API_KEY" not in namespace


def test_source_registry_exposes_only_phase1_sources():
    registry = get_source_registry()

    assert list(registry) == ["openalex", "crossref"]
    assert registry == SOURCE_REGISTRY

    openalex = registry["openalex"]
    crossref = registry["crossref"]

    assert openalex["source_type"] == "primary_ingest"
    assert crossref["source_type"] == "metadata_backfill"
    assert get_source_config("openalex") == openalex
    assert get_source_config("crossref") == crossref
    with pytest.raises(KeyError):
        get_source_config("dblp")

    assert openalex["auth"]["required"] is False
    assert openalex["auth"]["api_key_setting"] == "OPENALEX_API_KEY"
    assert crossref["auth"]["required"] is False
    assert crossref["auth"]["api_key_setting"] is None

    assert openalex["required_config_keys"] == [
        "DATA_ROOT",
        "OPENALEX_EMAIL",
        "OPENALEX_PAGE_SIZE",
        "OPENALEX_BACKOFF_SECONDS",
        "DEFAULT_MAX_RECORDS",
        "DEFAULT_MAX_PAGES",
        "DEFAULT_RETRY_LIMIT",
    ]
    assert crossref["required_config_keys"] == [
        "DATA_ROOT",
        "CROSSREF_MAILTO",
        "CROSSREF_PAGE_SIZE",
        "CROSSREF_BACKOFF_SECONDS",
        "DEFAULT_MAX_RECORDS",
        "DEFAULT_MAX_PAGES",
        "DEFAULT_RETRY_LIMIT",
    ]
    assert openalex["supported_operations"] == ["discover", "stage_raw"]
    assert crossref["supported_operations"] == ["backfill_raw"]
    assert openalex["polite_contact"]["email_setting"] == "OPENALEX_EMAIL"
    assert crossref["polite_contact"]["mailto_setting"] == "CROSSREF_MAILTO"
    assert openalex["retry"]["limit_setting"] == "DEFAULT_RETRY_LIMIT"
    assert crossref["retry"]["limit_setting"] == "DEFAULT_RETRY_LIMIT"
    assert openalex["retry"]["backoff_setting"] == "OPENALEX_BACKOFF_SECONDS"
    assert crossref["retry"]["backoff_setting"] == "CROSSREF_BACKOFF_SECONDS"
    assert openalex["rate_limit"]["requests_per_second"] > 0
    assert crossref["rate_limit"]["requests_per_second"] > 0
    assert openalex["raw_paths"] == {
        "works": "data/runs/{run_id}/openalex/works_raw.jsonl",
        "authors": "data/runs/{run_id}/openalex/authors_raw.jsonl",
    }
    assert crossref["raw_paths"] == {
        "works_backfill": "data/runs/{run_id}/crossref/works_backfill_raw.jsonl",
    }
    assert validate_source_selection(None) == ("openalex",)
    assert validate_source_selection(["crossref"]) == ("crossref",)

    with pytest.raises(ValueError):
        validate_source_selection(["openalex", "dblp"])


def test_run_context_creates_manifest_and_paths(tmp_path):
    manifest = build_run_manifest(
        run_id="run-20260413-0001",
        source_name="openalex",
        slice_type="concept",
        slice_value="artificial intelligence",
        since_year=2023,
        max_records=50,
        max_pages=2,
        default_retry_limit=3,
        sources_requested=("openalex",),
        config_fingerprint="fingerprint-123",
    )
    assert isinstance(manifest, RunManifest)
    manifest_dict = manifest.to_dict()
    assert manifest_dict["source_name"] == "openalex"
    assert manifest_dict["slice"] == {"type": "concept", "value": "artificial intelligence"}
    assert manifest_dict["limits"] == {"max_records": 50, "max_pages": 2}
    assert manifest_dict["retries"] == {"default_retry_limit": 3}
    assert manifest_dict["query_hash"]
    assert manifest_dict["parent_run_id"] is None

    ctx = create_run_context(
        data_root=tmp_path / "data",
        run_id=manifest.run_id,
        preset_type=manifest.slice_type,
        preset_value=manifest.slice_value,
        since_year=manifest.since_year,
        max_records=manifest.max_records,
        max_pages=manifest.max_pages,
        default_retry_limit=manifest.default_retry_limit,
        sources_requested=manifest.sources_requested,
        config_fingerprint=manifest.config_fingerprint,
    )

    manifest = ctx.initialize()

    assert isinstance(ctx, RunContext)
    assert ctx.run_dir == tmp_path / "data" / "runs" / "run-20260413-0001"
    assert ctx.manifest_path == ctx.run_dir / "run.json"
    assert ctx.latest_dir == tmp_path / "data" / "latest"
    assert ctx.source_dir("openalex") == ctx.run_dir / "openalex"
    assert ctx.source_dir("crossref") == ctx.run_dir / "crossref"
    assert ctx.raw_path("openalex", "works_raw.jsonl") == ctx.run_dir / "openalex" / "works_raw.jsonl"
    assert ctx.raw_path("crossref", "works_backfill_raw.jsonl") == ctx.run_dir / "crossref" / "works_backfill_raw.jsonl"
    assert ctx.checkpoint_path("openalex") == ctx.run_dir / "checkpoints" / "openalex.json"

    assert manifest["run_id"] == "run-20260413-0001"
    assert manifest["status"] == "running"
    assert manifest["source_name"] == "openalex"
    assert manifest["slice"] == {"type": "concept", "value": "artificial intelligence"}
    assert manifest["since_year"] == 2023
    assert manifest["limits"] == {"max_records": 50, "max_pages": 2}
    assert manifest["retries"] == {"default_retry_limit": 3}
    assert manifest["sources_requested"] == ["openalex"]
    assert manifest["sources_completed"] == []
    assert manifest["config_fingerprint"] == "fingerprint-123"
    assert manifest["parent_run_id"] is None
    assert manifest["source_attempts"] == {}
    assert manifest["completed_at"] is None
    assert "created_at" in manifest
    assert "query_hash" in manifest

    assert ctx.manifest_path.exists()
    assert (ctx.latest_dir / "run.json").exists()
    assert (ctx.run_dir / "checkpoints").is_dir()
    assert (ctx.run_dir / "openalex").is_dir()
    assert (ctx.run_dir / "crossref").is_dir()


def test_raw_envelope_and_append_only_jsonl(tmp_path):
    ctx = create_run_context(
        data_root=tmp_path / "data",
        run_id="run-20260413-0002",
        preset_type="venue",
        preset_value="NeurIPS",
        since_year=2024,
        max_records=2,
        max_pages=1,
        default_retry_limit=3,
        sources_requested=("openalex",),
        config_fingerprint="fingerprint-456",
    )
    ctx.initialize()

    raw_path = ctx.raw_path("openalex", "works_raw.jsonl")
    latest_path = ctx.latest_raw_path("openalex", "works_raw.jsonl")

    first = build_raw_envelope(
        run_id=ctx.run_id,
        source_id="openalex",
        entity_type="works",
        source_record_id="W1",
        slice_definition={"type": "venue", "value": "NeurIPS"},
        checkpoint_cursor="cursor-1",
        raw={"id": "W1"},
    )
    second = build_raw_envelope(
        run_id=ctx.run_id,
        source_id="openalex",
        entity_type="works",
        source_record_id="W2",
        slice_definition={"type": "venue", "value": "NeurIPS"},
        checkpoint_cursor="cursor-2",
        raw={"id": "W2"},
    )

    assert first["run_id"] == ctx.run_id
    assert first["source"] == "openalex"
    assert first["entity_type"] == "works"
    assert first["source_record_id"] == "W1"
    assert first["slice"] == {"type": "venue", "value": "NeurIPS"}
    assert first["checkpoint_cursor"] == "cursor-1"
    assert first["raw"] == {"id": "W1"}
    assert "fetched_at" in first
    assert "payload" not in first

    stage_record(raw_path, first, mirror_path=latest_path)
    stage_records(raw_path, [second], mirror_path=latest_path)

    lines = raw_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["raw"] == {"id": "W1"}
    assert json.loads(lines[1])["raw"] == {"id": "W2"}
    assert latest_path.exists()
    assert json.loads(latest_path.read_text(encoding="utf-8").splitlines()[0])["raw"] == {"id": "W1"}


def test_source_attempt_serializes_into_manifest(tmp_path):
    ctx = create_run_context(
        data_root=tmp_path / "data",
        run_id="run-20260413-0003",
        preset_type="keyword",
        preset_value="transformer",
        since_year=2024,
        max_records=5,
        max_pages=1,
        default_retry_limit=3,
        sources_requested=("openalex", "crossref"),
        config_fingerprint="fingerprint-789",
    )
    ctx.initialize()

    attempt = SourceAttempt(
        request_params={"preset_type": "keyword", "preset_value": "transformer"},
        retry_count=2,
        checkpoint_cursor="cursor-99",
        page_count=4,
        record_count=12,
        error_summary="",
    )
    ctx.record_source_attempt("openalex", attempt)
    ctx.complete_source("openalex")
    manifest = ctx.write_manifest(status="completed", completed_at="2026-04-13T12:00:00Z")

    assert manifest["status"] == "completed"
    assert manifest["sources_completed"] == ["openalex"]
    assert manifest["source_attempts"]["openalex"] == {
        "request_params": {"preset_type": "keyword", "preset_value": "transformer"},
        "retry_count": 2,
        "checkpoint_cursor": "cursor-99",
        "page_count": 4,
        "record_count": 12,
        "error_summary": "",
    }
    saved_manifest = json.loads(ctx.manifest_path.read_text(encoding="utf-8"))
    assert saved_manifest["status"] == "completed"
    assert saved_manifest["source_attempts"]["openalex"]["record_count"] == 12
