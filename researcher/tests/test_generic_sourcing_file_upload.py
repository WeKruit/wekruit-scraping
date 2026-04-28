import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import sourcing_upload_file

FIXTURES = ROOT / "researcher" / "tests" / "fixtures" / "sourcing"


def test_devpost_json_converts_project_and_member_records():
    projects = json.loads((FIXTURES / "devpost_projects.json").read_text(encoding="utf-8"))
    records = sourcing_upload_file.to_source_records(
        run_id="devpost-run",
        domain="hackathon",
        source="devpost",
        records=projects,
    )

    assert [record["entityType"] for record in records] == ["project", "person", "project", "person"]
    assert {record["domain"] for record in records} == {"hackathon"}
    assert {record["source"] for record in records} == {"devpost"}
    assert "displayName" not in records[0]
    assert "institution" not in records[0]
    assert records[0]["rawSummary"]["github"] == ["https://github.com/alex-rivera-ai/vision-assist"]
    assert records[0]["rawSummary"]["prizes"] == ["Accessibility Winner"]
    assert records[0]["rawSummary"]["suggestedSignals"] == [
        "technical_project",
        "hackathon_participation",
        "award_or_recognition",
        "builder_signal",
    ]
    assert records[1]["displayName"] == "Alex Rivera"
    assert records[1]["rawSummary"]["github"] == "https://github.com/alex-rivera-ai"
    assert records[1]["rawSummary"]["projectName"] == "Vision Assist"
    assert records[1]["rawSummary"]["tech"] == ["python", "computer-vision", "accessibility"]
    assert "founder_or_builder_signal" in records[1]["rawSummary"]["suggestedSignals"]
    assert records[1]["rawStoragePath"].startswith("sourcing/raw/hackathon/devpost/devpost-run/")


def test_github_candidate_converts_contact_and_profile_evidence():
    candidates = json.loads((FIXTURES / "github_candidates.json").read_text(encoding="utf-8"))
    records = sourcing_upload_file.to_source_records(
        run_id="github-run",
        domain="developer",
        source="github",
        records=candidates,
    )

    assert len(records) == 2
    record = records[0]
    assert record["entityType"] == "person"
    assert record["displayName"] == "Alex Rivera"
    assert record["institution"] == "Example University"
    assert record["rawSummary"]["email"] == "alex.rivera@example.edu"
    assert record["rawSummary"]["github"] == "https://github.com/alex-rivera-ai"
    assert record["rawSummary"]["mergedPrs"] == 24
    assert record["rawSummary"]["repoCount"] == 2
    assert record["rawSummary"]["projectStars"] == 1540
    assert record["rawSummary"]["sourceRepos"] == ["vision/assist", "robotics/perception-kit"]
    assert record["rawSummary"]["suggestedSignals"] == [
        "open_source_contribution",
        "technical_project",
        "high_activity",
        "maintainer_or_influence_signal",
    ]


def test_research_json_preserves_orcid_doi_and_academic_signals():
    records = sourcing_upload_file.to_source_records(
        run_id="research-run",
        domain="researcher",
        source="openalex",
        records=json.loads((FIXTURES / "research_records.json").read_text(encoding="utf-8")),
    )

    assert len(records) == 3
    first = records[0]
    assert first["entityType"] == "person"
    assert first["displayName"] == "Taylor Chen"
    assert first["institution"] == "Open Systems Institute"
    assert first["sourceUrl"] == "https://taylorchen.example.org"
    assert first["rawSummary"]["orcid"] == "0000-0002-1825-0097"
    assert first["rawSummary"]["doi"] == "10.1234/example.2026.001"
    assert first["rawSummary"]["venue"] == "NeurIPS"
    assert first["rawSummary"]["suggestedSignals"] == [
        "research_publication",
        "education_affiliation",
        "academic_research_signal",
    ]


def test_csv_manual_upload_dry_run_writes_source_records(tmp_path):
    input_path = tmp_path / "manual.csv"
    with input_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "email", "github_url", "company"])
        writer.writeheader()
        writer.writerow({
            "name": "Lin Reviewer",
            "email": "lin@example.edu",
            "github_url": "https://github.com/lin",
            "company": "Review Lab",
        })

    exit_code = sourcing_upload_file.main([
        "--input",
        str(input_path),
        "--run-id",
        "manual-run",
        "--domain",
        "manual",
        "--source",
        "csv",
        "--output-root",
        str(tmp_path / "data"),
        "--dry-run",
    ])

    assert exit_code == 0
    records_path = tmp_path / "data" / "runs" / "manual-run" / "sourcing" / "source_records.jsonl"
    records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1
    assert records[0]["rawSummary"]["email"] == "lin@example.edu"
    assert records[0]["rawSummary"]["github"] == "https://github.com/lin"
