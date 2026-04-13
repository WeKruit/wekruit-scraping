import json
from pathlib import Path

import pytest

from pipeline.raw_staging import build_raw_envelope, stage_record
from pipeline.run_context import create_run_context


ROOT = Path(__file__).resolve().parents[1]
CROSSREF_FIXTURE = ROOT / "tests" / "fixtures" / "crossref" / "work.json"


def _load_crossref_fixture() -> dict:
    return json.loads(CROSSREF_FIXTURE.read_text(encoding="utf-8"))


def _seed_openalex_run(data_root: Path) -> Path:
    ctx = create_run_context(
        data_root=data_root,
        run_id="run-openalex-001",
        preset_type="venue",
        preset_value="NeurIPS",
        since_year=2024,
        max_records=5,
        max_pages=1,
        default_retry_limit=3,
        sources_requested=("openalex",),
        config_fingerprint="seed-openalex",
    )
    ctx.initialize()
    works_path = ctx.raw_path("openalex", "works_raw.jsonl")
    stage_record(
        works_path,
        build_raw_envelope(
            run_id=ctx.run_id,
            source_id="openalex",
            entity_type="works",
            source_record_id="https://openalex.org/W1",
            slice_definition={"type": "venue", "value": "NeurIPS"},
            checkpoint_cursor="cursor-1",
            raw={
                "id": "https://openalex.org/W1",
                "doi": "https://doi.org/10.1000/example1",
                "title": "Transformer Models for AI",
            },
        ),
    )
    stage_record(
        works_path,
        build_raw_envelope(
            run_id=ctx.run_id,
            source_id="openalex",
            entity_type="works",
            source_record_id="https://openalex.org/W2",
            slice_definition={"type": "venue", "value": "NeurIPS"},
            checkpoint_cursor="cursor-1",
            raw={
                "id": "https://openalex.org/W2",
                "doi": None,
                "title": "No DOI example",
            },
        ),
    )
    ctx.complete_source("openalex")
    ctx.write_manifest(status="completed")
    return works_path


def test_crossref_backfill_requires_upstream_openalex_run(tmp_path):
    from scripts import s1_crossref_backfill

    with pytest.raises(SystemExit):
        s1_crossref_backfill.main(["--input-run", "missing-run", "--output-root", str(tmp_path / "data")])


def test_crossref_backfill_stages_only_doi_records(tmp_path, monkeypatch):
    from scripts import s1_crossref_backfill
    from sources.crossref import CrossrefAdapter

    data_root = tmp_path / "data"
    _seed_openalex_run(data_root)
    staged = []

    def fake_fetch_work(self, doi: str):
        assert doi == "10.1000/example1"
        return _load_crossref_fixture()

    def fake_stage_records(path, records, *, mirror_path=None):
        staged.append((Path(path), [record["source_record_id"] for record in records]))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n", encoding="utf-8")
        if mirror_path is not None:
            mirror_path.parent.mkdir(parents=True, exist_ok=True)
            mirror_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        return Path(path)

    monkeypatch.setattr(CrossrefAdapter, "fetch_work", fake_fetch_work)
    monkeypatch.setattr(s1_crossref_backfill, "stage_records", fake_stage_records)

    exit_code = s1_crossref_backfill.main(
        ["--input-run", "run-openalex-001", "--output-root", str(data_root), "--run-id", "run-crossref-001"]
    )

    assert exit_code == 0
    assert staged == [
        (
            data_root / "runs" / "run-crossref-001" / "crossref" / "works_backfill_raw.jsonl",
            ["10.1000/example1"],
        )
    ]

    manifest = json.loads((data_root / "runs" / "run-crossref-001" / "run.json").read_text(encoding="utf-8"))
    assert manifest["source_name"] == "crossref"
    assert manifest["parent_run_id"] == "run-openalex-001"
    assert manifest["sources_completed"] == ["crossref"]
    assert manifest["source_attempts"]["crossref"]["request_params"]["input_run"] == "run-openalex-001"
    assert manifest["source_attempts"]["crossref"]["request_params"]["skipped_no_doi"] == 1
    assert manifest["source_attempts"]["crossref"]["record_count"] == 1
    assert manifest["source_attempts"]["crossref"]["checkpoint_cursor"] == "10.1000/example1"


def test_crossref_resume_skips_seen_dois(tmp_path, monkeypatch):
    from pipeline.incremental_state import write_seen_ids
    from scripts import s1_crossref_backfill
    from sources.crossref import CrossrefAdapter

    data_root = tmp_path / "data"
    _seed_openalex_run(data_root)
    write_seen_ids(data_root, lineage_key="run-openalex-001", source_id="crossref", values={"10.1000/example1"})

    def fail_fetch(self, doi: str):
        raise AssertionError(f"Crossref fetch should not run for {doi}")

    monkeypatch.setattr(CrossrefAdapter, "fetch_work", fail_fetch)

    exit_code = s1_crossref_backfill.main(
        [
            "--input-run",
            "run-openalex-001",
            "--output-root",
            str(data_root),
            "--run-id",
            "run-crossref-002",
            "--resume-lineage",
        ]
    )

    assert exit_code == 0
    manifest = json.loads((data_root / "runs" / "run-crossref-002" / "run.json").read_text(encoding="utf-8"))
    assert manifest["source_attempts"]["crossref"]["record_count"] == 0
    assert manifest["source_attempts"]["crossref"]["request_params"]["skipped_existing"] == 1


def test_openalex_replay_avoids_network_calls(tmp_path, monkeypatch):
    from scripts import s1_openalex_fetch
    from sources.openalex import OpenAlexAdapter

    data_root = tmp_path / "data"
    _seed_openalex_run(data_root)

    def fail_fetch(self, query, *, cursor=None):
        raise AssertionError("Replay path should not fetch OpenAlex pages")

    monkeypatch.setattr(OpenAlexAdapter, "fetch_page", fail_fetch)

    exit_code = s1_openalex_fetch.main(
        [
            "--preset-type",
            "venue",
            "--preset",
            "neurips",
            "--since",
            "2024",
            "--output-root",
            str(data_root),
            "--replay-run",
            "run-openalex-001",
        ]
    )

    assert exit_code == 0
