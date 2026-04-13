import json
from pathlib import Path

import pytest

from pipeline.run_context import create_run_context


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "openalex" / "works_page.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_ai_ml_presets_are_explicit_and_named():
    from presets.ai_ml import PRESET_FAMILIES, get_preset, list_presets

    assert list(PRESET_FAMILIES) == ["venue", "concept", "keyword"]
    assert list_presets("venue") == ["neurips", "iclr"]
    assert list_presets("concept") == ["artificial-intelligence", "machine-learning"]
    assert list_presets("keyword") == ["transformer", "attention"]

    preset = get_preset("venue", "neurips")
    assert preset["family"] == "venue"
    assert preset["slug"] == "neurips"
    assert preset["label"] == "NeurIPS"
    assert preset["query"] == "NeurIPS"
    assert preset["filter"] == {"primary_location.source.display_name": "NeurIPS"}
    assert preset["entity"] == "works"

    concept = get_preset("concept", "artificial-intelligence")
    assert concept["filter"] == {"concepts.id": "C154945302"}
    keyword = get_preset("keyword", "transformer")
    assert keyword["search"] == "transformer"


def test_openalex_adapter_builds_query_and_parses_fixture():
    from presets.ai_ml import get_preset
    from sources.openalex import OpenAlexAdapter

    page = _load_fixture()
    adapter = OpenAlexAdapter()
    preset = get_preset("venue", "neurips")

    query = adapter.build_query(preset, since_year=2024, max_records=2, max_pages=1)
    assert query["params"]["search"] == "NeurIPS"
    assert query["params"]["filter"] == "primary_location.source.display_name:NeurIPS,from_publication_date:2024-01-01"
    assert query["params"]["per-page"] == 2
    assert query["params"]["cursor"] == "*"

    works, authors = adapter.parse_page(page["results"], preset=preset, run_id="run-1")
    assert [work["source_record_id"] for work in works] == ["https://openalex.org/W1", "https://openalex.org/W2"]
    assert works[0]["raw"]["title"] == "Transformer Models for AI"
    assert works[1]["slice"] == {"type": "venue", "value": "NeurIPS"}

    author_ids = [author["source_record_id"] for author in authors]
    assert author_ids == ["https://openalex.org/A1", "https://openalex.org/A2"]
    assert authors[0]["raw"]["paper_count_in_batch"] == 2
    assert authors[0]["raw"]["institution"] == "Institute of AI"
    assert authors[1]["raw"]["paper_count_in_batch"] == 1


def test_cli_stages_work_and_author_records_offline(tmp_path, monkeypatch):
    from config import source_registry
    from scripts import s1_openalex_fetch
    from sources.openalex import OpenAlexAdapter

    page = _load_fixture()
    staged = []

    def fake_fetch_page(self, query, *, cursor=None):
        assert query["params"]["search"] == "NeurIPS"
        assert cursor == "*"
        return page

    def fake_stage_records(path, records, *, mirror_path=None):
        staged.append((Path(path), [record["source_record_id"] for record in records], Path(mirror_path) if mirror_path else None))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n", encoding="utf-8")
        if mirror_path is not None:
            mirror_path.parent.mkdir(parents=True, exist_ok=True)
            mirror_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        return Path(path)

    monkeypatch.setattr(OpenAlexAdapter, "fetch_page", fake_fetch_page)
    monkeypatch.setattr(s1_openalex_fetch, "stage_records", fake_stage_records)
    monkeypatch.setattr(s1_openalex_fetch, "create_run_context", create_run_context)
    monkeypatch.setattr(source_registry, "validate_source_selection", source_registry.validate_source_selection)

    exit_code = s1_openalex_fetch.main([
        "--preset-type",
        "venue",
        "--preset",
        "neurips",
        "--since",
        "2024",
        "--max-records",
        "2",
        "--max-pages",
        "1",
        "--output-root",
        str(tmp_path / "data"),
        "--run-id",
        "run-20260413-0101",
    ])

    assert exit_code == 0
    assert len(staged) == 2
    assert staged[0][0].name == "works_raw.jsonl"
    assert staged[1][0].name == "authors_raw.jsonl"
    assert staged[0][1] == ["https://openalex.org/W1", "https://openalex.org/W2"]
    assert staged[1][1] == ["https://openalex.org/A1", "https://openalex.org/A2"]

    run_dir = tmp_path / "data" / "runs" / "run-20260413-0101"
    assert (run_dir / "run.json").exists()
    assert (run_dir / "openalex" / "works_raw.jsonl").exists()
    assert (run_dir / "openalex" / "authors_raw.jsonl").exists()

    manifest = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    assert manifest["sources_completed"] == ["openalex"]
    assert manifest["source_attempts"]["openalex"]["request_params"] == {
        "preset_type": "venue",
        "preset": "neurips",
        "since": 2024,
    }
    assert manifest["source_attempts"]["openalex"]["page_count"] == 1
    assert manifest["source_attempts"]["openalex"]["record_count"] == 2
    assert manifest["source_attempts"]["openalex"]["checkpoint_cursor"] == "cursor-2"
