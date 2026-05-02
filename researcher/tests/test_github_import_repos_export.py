import json
import sys
import zipfile
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
GITHUB_ROOT = ROOT / "github"
if str(GITHUB_ROOT) not in sys.path:
    sys.path.insert(0, str(GITHUB_ROOT))

from github import github_import_repos_export
from github.github_scorer import GitHubScorer


GITHUB_REPO_HEADERS = [
    "full_name",
    "stars",
    "language",
    "description",
    "topics",
    "sources",
    "created_at",
    "pushed_at",
    "html_url",
    "discovered_at",
]


def _write_repos_workbook(path: Path, rows: list[dict[str, object]]) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(GITHUB_REPO_HEADERS)
    for row in rows:
        worksheet.append([row.get(header, "") for header in GITHUB_REPO_HEADERS])
    workbook.save(path)


def test_github_repo_export_zip_converts_to_existing_repos_contract(tmp_path):
    workbook_path = tmp_path / "repos.xlsx"
    _write_repos_workbook(
        workbook_path,
        [
            {
                "full_name": "team/vision-agent",
                "stars": 150,
                "language": "Python",
                "description": "Vision agent tools",
                "topics": "ai | agents | computer-vision",
                "sources": "search:application | topic:agents",
                "created_at": "2025-01-01",
                "pushed_at": "2026-04-01",
                "html_url": "https://github.com/team/vision-agent",
                "discovered_at": "2026-04-06",
            },
            {
                "full_name": "team/vision-agent",
                "stars": "175.0",
                "language": "Python",
                "topics": "ai | accessibility",
                "sources": "topic:ai",
                "html_url": "https://github.com/team/vision-agent",
            },
            {
                "full_name": "team/noise",
                "stars": 10,
                "language": "Go",
                "html_url": "https://github.com/team/noise",
            },
        ],
    )
    zip_path = tmp_path / "github.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.write(workbook_path, "github/repos.xlsx")

    output_path = tmp_path / "repos.json"
    exit_code = github_import_repos_export.main(
        [
            "--input",
            str(zip_path),
            "--output",
            str(output_path),
            "--min-stars",
            "100",
        ]
    )

    assert exit_code == 0
    repos = json.loads(output_path.read_text(encoding="utf-8"))
    assert repos == [
        {
            "full_name": "team/vision-agent",
            "html_url": "https://github.com/team/vision-agent",
            "stars": 175,
            "language": "Python",
            "description": "Vision agent tools",
            "topics": ["ai", "agents", "computer-vision", "accessibility"],
            "sources": ["search:application", "topic:agents", "topic:ai"],
            "created_at": "2025-01-01",
            "pushed_at": "2026-04-01",
            "discovered_at": "2026-04-06",
        }
    ]


def test_github_repo_export_can_select_exact_repo_from_html_url(tmp_path):
    workbook_path = tmp_path / "repos.xlsx"
    _write_repos_workbook(
        workbook_path,
        [
            {
                "stars": 999,
                "language": "TypeScript",
                "html_url": "https://github.com/org/from-url",
                "topics": "llm | workflow",
                "sources": "search:frontier",
            },
            {
                "full_name": "org/other",
                "stars": 1000,
                "language": "TypeScript",
                "html_url": "https://github.com/org/other",
            },
        ],
    )

    output_path = tmp_path / "repos.json"
    github_import_repos_export.main(
        [
            "--input",
            str(workbook_path),
            "--output",
            str(output_path),
            "--repo",
            "org/from-url",
        ]
    )

    repos = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(repos) == 1
    assert repos[0]["full_name"] == "org/from-url"
    assert repos[0]["topics"] == ["llm", "workflow"]
    assert repos[0]["sources"] == ["search:frontier"]


def test_github_scorer_writes_custom_output_directory(tmp_path):
    scorer = GitHubScorer(threshold=0)
    candidates = [
        {
            "username": "ada-dev",
            "repos": [{"full_name": "team/vision-agent", "stars": 500, "commits": 12}],
            "total_commits": 12,
            "profile": {
                "name": "Ada Dev",
                "bio": "Builds AI tools",
                "company": "Example Lab",
                "location": "Remote",
                "public_repos": 10,
                "followers": 75,
                "updated_at": "2026-04-01T00:00:00Z",
                "html_url": "https://github.com/ada-dev",
            },
            "emails": ["ada@example.com"],
        }
    ]
    scored = scorer.score_all(candidates)
    json_path = tmp_path / "scored" / "scored_candidates.json"
    csv_path = tmp_path / "scored" / "scored_candidates.csv"

    scorer.save(scored, json_path=str(json_path), csv_path=str(csv_path))

    assert json_path.exists()
    assert csv_path.exists()
