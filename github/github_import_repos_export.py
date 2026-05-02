#!/usr/bin/env python3
"""Convert Drive-exported GitHub repository workbooks into repos.json.

The GitHub contributor pipeline expects the same repository contract emitted by
github_discover.py. This helper adapts the Drive export format into that
contract without changing contributor extraction or scoring behavior.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.sourcing_upload_file import first_non_empty, load_input_records


DEFAULT_OUTPUT = ROOT / "github" / "output" / "repos.json"


def text_value(value: Any) -> str:
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def iso_value(value: Any) -> str:
    if isinstance(value, datetime):
        return value.replace(microsecond=0).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return text_value(value)


def int_value(value: Any) -> int:
    if value in (None, "", [], {}):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(str(value).strip()))
        except (TypeError, ValueError):
            return 0


def split_multi_value(value: Any) -> list[str]:
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            parts.extend(split_multi_value(item))
        return unique_strings(parts)

    text = text_value(value)
    if not text:
        return []

    parts = [text]
    for separator in ("|", ";", "\n"):
        next_parts: list[str] = []
        for part in parts:
            next_parts.extend(part.split(separator))
        parts = next_parts
    return unique_strings(part.strip() for part in parts if part.strip())


def unique_strings(values: Iterable[Any]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        text = text_value(value)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(text)
    return output


def repo_name_from_url(value: Any) -> str:
    text = text_value(value)
    if not text:
        return ""
    try:
        parsed = urlparse(text)
    except ValueError:
        return ""
    if "github.com" not in parsed.netloc.lower():
        return ""
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        return ""
    return f"{parts[0]}/{parts[1]}"


def normalize_repo_row(row: dict[str, Any]) -> dict[str, Any] | None:
    full_name = first_non_empty(row.get("full_name"), repo_name_from_url(row.get("html_url")))
    if not full_name or "/" not in full_name:
        return None

    html_url = first_non_empty(row.get("html_url"), f"https://github.com/{full_name}")
    return {
        "full_name": full_name,
        "html_url": html_url,
        "stars": int_value(row.get("stars")),
        "language": text_value(row.get("language")),
        "description": text_value(row.get("description"))[:500],
        "topics": split_multi_value(row.get("topics")),
        "sources": split_multi_value(row.get("sources")) or ["drive_export"],
        "created_at": iso_value(row.get("created_at")),
        "pushed_at": iso_value(row.get("pushed_at")),
        "discovered_at": iso_value(row.get("discovered_at")),
    }


def merge_repo(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    if incoming.get("stars", 0) > existing.get("stars", 0):
        existing["stars"] = incoming["stars"]
    existing["topics"] = unique_strings([*existing.get("topics", []), *incoming.get("topics", [])])
    existing["sources"] = unique_strings([*existing.get("sources", []), *incoming.get("sources", [])])
    for key in ("html_url", "language", "description", "created_at", "pushed_at", "discovered_at"):
        if not existing.get(key) and incoming.get(key):
            existing[key] = incoming[key]
    return existing


def normalize_repo_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    repos_by_key: dict[str, dict[str, Any]] = {}
    for row in rows:
        repo = normalize_repo_row(row)
        if not repo:
            continue
        key = repo["full_name"].lower()
        if key in repos_by_key:
            merge_repo(repos_by_key[key], repo)
        else:
            repos_by_key[key] = repo
    return list(repos_by_key.values())


def filter_repos(
    repos: Iterable[dict[str, Any]],
    *,
    min_stars: int = 0,
    languages: set[str] | None = None,
    source_contains: list[str] | None = None,
    selected_repos: set[str] | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    source_terms = [term.lower() for term in source_contains or [] if term]
    output: list[dict[str, Any]] = []
    for repo in repos:
        if repo.get("stars", 0) < min_stars:
            continue
        if languages and repo.get("language", "").lower() not in languages:
            continue
        if selected_repos and repo.get("full_name", "").lower() not in selected_repos:
            continue
        if source_terms:
            haystack = " ".join(repo.get("sources", [])).lower()
            if not any(term in haystack for term in source_terms):
                continue
        output.append(repo)
        if limit is not None and len(output) >= limit:
            break
    return output


def write_repos_json(repos: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(repos, ensure_ascii=False, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert GitHub Drive repo exports into github/output/repos.json.")
    parser.add_argument("--input", required=True, type=Path, help="GitHub export .zip, .xlsx, .csv, .json, or directory")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--min-stars", type=int, default=0)
    parser.add_argument("--language", action="append", default=[], help="Keep a language, repeatable")
    parser.add_argument("--source-contains", action="append", default=[], help="Keep repos whose source tag contains this term")
    parser.add_argument("--repo", action="append", default=[], help="Keep an exact owner/name repo, repeatable")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Print summary without writing output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = load_input_records(args.input)
    repos = normalize_repo_rows(rows)
    filtered = filter_repos(
        repos,
        min_stars=args.min_stars,
        languages={language.lower() for language in args.language} if args.language else None,
        source_contains=args.source_contains,
        selected_repos={repo.lower() for repo in args.repo} if args.repo else None,
        limit=args.limit,
    )

    print(f"loaded rows: {len(rows)}")
    print(f"normalized repos: {len(repos)}")
    print(f"selected repos: {len(filtered)}")
    if filtered:
        top = filtered[0]
        print(f"top repo: {top['full_name']} ({top.get('stars', 0)} stars)")

    if args.dry_run:
        return 0

    write_repos_json(filtered, args.output)
    print(f"wrote repos: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
