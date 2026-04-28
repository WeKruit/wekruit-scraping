import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import sourcing_upload_file


def test_devpost_json_converts_project_and_member_records():
    records = sourcing_upload_file.to_source_records(
        run_id="devpost-run",
        domain="hackathon",
        source="devpost",
        records=[
            {
                "name": "Agent Builder",
                "project_url": "https://devpost.com/software/agent-builder",
                "hackathon": "TreeHacks",
                "github_links": ["https://github.com/example/agent-builder"],
                "members": [
                    {
                        "name": "Ada Maker",
                        "devpost_profile": "https://devpost.com/ada",
                        "github_url": "https://github.com/ada",
                        "linkedin_url": "https://linkedin.com/in/ada",
                    }
                ],
            }
        ],
    )

    assert [record["entityType"] for record in records] == ["project", "person"]
    assert {record["domain"] for record in records} == {"hackathon"}
    assert {record["source"] for record in records} == {"devpost"}
    assert "displayName" not in records[0]
    assert "institution" not in records[0]
    assert records[0]["rawSummary"]["github"] == ["https://github.com/example/agent-builder"]
    assert records[1]["rawSummary"]["github"] == "https://github.com/ada"
    assert records[1]["rawStoragePath"].startswith("sourcing/raw/hackathon/devpost/devpost-run/")


def test_github_candidate_converts_contact_and_profile_evidence():
    records = sourcing_upload_file.to_source_records(
        run_id="github-run",
        domain="developer",
        source="github",
        records=[
            {
                "username": "grace",
                "emails": ["grace@example.edu"],
                "total_commits": 42,
                "profile": {
                    "name": "Grace Hopper",
                    "company": "Compiler Lab",
                    "blog": "https://grace.example.edu",
                    "html_url": "https://github.com/grace",
                    "followers": 100,
                    "public_repos": 12,
                },
            }
        ],
    )

    assert len(records) == 1
    record = records[0]
    assert record["entityType"] == "person"
    assert record["displayName"] == "Grace Hopper"
    assert record["institution"] == "Compiler Lab"
    assert record["rawSummary"]["email"] == "grace@example.edu"
    assert record["rawSummary"]["github"] == "https://github.com/grace"


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
