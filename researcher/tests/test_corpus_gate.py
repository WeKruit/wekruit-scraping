from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pipeline.corpus_gate import run_corpus_gate
from pipeline.run_context import build_derived_run_manifest, create_run_context
from pipeline.raw_staging import stage_records
from pipeline.venue_tiers import DEFAULT_VENUE_TIER_ASSET, hash_venue_tier_asset


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "corpus_gate" / "works_raw.jsonl"
EXPECTED_DECISIONS = ROOT / "tests" / "fixtures" / "corpus_gate" / "expected_gate_decisions.jsonl"


def _stage_parent_run(tmp_path: Path, run_id: str) -> tuple[str, Path]:
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
        config_fingerprint="fingerprint-parent",
    )
    ctx.initialize()
    parent_works_path = ctx.raw_path("openalex", "works_raw.jsonl")
    stage_records(parent_works_path, [
        json.loads(line)
        for line in FIXTURE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ])
    return ctx.run_id, parent_works_path


def test_derived_manifest_and_lineage(tmp_path):
    manifest = build_derived_run_manifest(
        stage_name="corpus_gate",
        run_id="gate-run-1",
        parent_run_id="input-run-1",
        input_paths={"works_raw.jsonl": "data/runs/input-run-1/openalex/works_raw.jsonl"},
        output_paths={
            "gated_works.jsonl": "data/runs/gate-run-1/corpus_gate/gated_works.jsonl",
            "gate_decisions.jsonl": "data/runs/gate-run-1/corpus_gate/gate_decisions.jsonl",
        },
        asset_fingerprints={"ai_cs_venue_tiers.csv": "hash-123"},
        included_count=1,
        excluded_count=3,
    )

    assert manifest.to_dict() == {
        "stage_name": "corpus_gate",
        "run_id": "gate-run-1",
        "parent_run_id": "input-run-1",
        "input_paths": {"works_raw.jsonl": "data/runs/input-run-1/openalex/works_raw.jsonl"},
        "output_paths": {
            "gated_works.jsonl": "data/runs/gate-run-1/corpus_gate/gated_works.jsonl",
            "gate_decisions.jsonl": "data/runs/gate-run-1/corpus_gate/gate_decisions.jsonl",
        },
        "asset_fingerprints": {"ai_cs_venue_tiers.csv": "hash-123"},
        "included_count": 1,
        "excluded_count": 3,
        "created_at": manifest.created_at,
        "completed_at": None,
        "status": "running",
    }


def test_gate_cli_writes_only_included_works_and_decisions(tmp_path):
    _stage_parent_run(tmp_path, "input-run-1")

    result = run_corpus_gate(
        data_root=tmp_path / "data",
        input_run_id="input-run-1",
        run_id="gate-run-1",
    )

    output_path = result["output_path"]
    decision_path = result["decision_path"]
    manifest_path = result["manifest_path"]

    assert result["included_count"] == 1
    assert result["excluded_count"] == 3
    assert output_path == tmp_path / "data" / "runs" / "gate-run-1" / "corpus_gate" / "gated_works.jsonl"
    assert decision_path == tmp_path / "data" / "runs" / "gate-run-1" / "corpus_gate" / "gate_decisions.jsonl"
    assert manifest_path == tmp_path / "data" / "runs" / "gate-run-1" / "corpus_gate" / "run.json"

    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])

    assert record["source_record_id"] == "https://openalex.org/W1000000001"
    assert record["gate_run_id"] == "gate-run-1"
    assert record["parent_run_id"] == "input-run-1"
    assert record["venue_row_slug"] == "neurips"
    assert record["normalized_tier"] == "T1"
    assert record["corpus_gate"]["decision"] == "include"
    assert record["corpus_gate"]["reason_code"] == "matched_ai_cs_venue_tier"
    assert record["corpus_gate"]["matched_source_id"] == "https://openalex.org/S4306420609"
    assert record["corpus_gate"]["venue_row_slug"] == "neurips"
    assert record["corpus_gate"]["normalized_tier"] == "T1"
    assert record["corpus_gate"]["venue_asset_fingerprint"]

    assert decision_path.read_text(encoding="utf-8").splitlines() == EXPECTED_DECISIONS.read_text(encoding="utf-8").splitlines()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["stage_name"] == "corpus_gate"
    assert manifest["run_id"] == "gate-run-1"
    assert manifest["parent_run_id"] == "input-run-1"
    assert manifest["included_count"] == 1
    assert manifest["excluded_count"] == 3
    assert manifest["status"] == "completed"
    assert manifest["output_paths"]["gated_works.jsonl"] == str(output_path)
    assert manifest["output_paths"]["gate_decisions.jsonl"] == str(decision_path)
    assert manifest["input_paths"]["works_raw.jsonl"].endswith("input-run-1/openalex/works_raw.jsonl")
    assert manifest["asset_fingerprints"]["ai_cs_venue_tiers.csv"] == hash_venue_tier_asset(DEFAULT_VENUE_TIER_ASSET)

def test_rerun_lineage_new_parent_run(tmp_path):
    _stage_parent_run(tmp_path, "input-run-1")
    first = run_corpus_gate(
        data_root=tmp_path / "data",
        input_run_id="input-run-1",
        run_id="gate-run-1",
    )
    first_gated = first["output_path"].read_text(encoding="utf-8")
    first_decisions = first["decision_path"].read_text(encoding="utf-8")

    _stage_parent_run(tmp_path, "input-run-2")
    second = run_corpus_gate(
        data_root=tmp_path / "data",
        input_run_id="input-run-2",
        run_id="gate-run-2",
    )

    assert second["parent_run_id"] == "input-run-2"
    assert second["gate_run_id"] == "gate-run-2"
    assert second["output_path"] != first["output_path"]
    assert second["decision_path"] != first["decision_path"]
    assert first["output_path"].read_text(encoding="utf-8") == first_gated
    assert first["decision_path"].read_text(encoding="utf-8") == first_decisions


def test_venue_table_hash_creates_new_run(tmp_path):
    _stage_parent_run(tmp_path, "input-run-1")
    first = run_corpus_gate(
        data_root=tmp_path / "data",
        input_run_id="input-run-1",
        run_id="gate-run-1",
    )
    first_manifest = json.loads(first["manifest_path"].read_text(encoding="utf-8"))
    first_gated = first["output_path"].read_text(encoding="utf-8")
    first_decisions = first["decision_path"].read_text(encoding="utf-8")

    altered_table = tmp_path / "altered_ai_cs_venue_tiers.csv"
    altered_table.write_text(DEFAULT_VENUE_TIER_ASSET.read_text(encoding="utf-8").replace(
        "CCF AI A and CORE ICORE2026 A*.",
        "CCF AI A and CORE ICORE2026 A* (revalidated).",
        1,
    ), encoding="utf-8")

    second = run_corpus_gate(
        data_root=tmp_path / "data",
        input_run_id="input-run-1",
        venue_table=altered_table,
        run_id="gate-run-2",
    )
    second_manifest = json.loads(second["manifest_path"].read_text(encoding="utf-8"))

    assert first_manifest["asset_fingerprints"]["ai_cs_venue_tiers.csv"] == hash_venue_tier_asset(DEFAULT_VENUE_TIER_ASSET)
    assert second_manifest["asset_fingerprints"]["altered_ai_cs_venue_tiers.csv"] == hash_venue_tier_asset(altered_table)
    assert first_manifest["asset_fingerprints"]["ai_cs_venue_tiers.csv"] != second_manifest["asset_fingerprints"]["altered_ai_cs_venue_tiers.csv"]
    assert first["output_path"].read_text(encoding="utf-8") == first_gated
    assert first["decision_path"].read_text(encoding="utf-8") == first_decisions


def test_gate_cli_help():
    proc = subprocess.run(
        [sys.executable, "scripts/s2_corpus_gate.py", "--help"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Phase 6 corpus gate" in proc.stdout
