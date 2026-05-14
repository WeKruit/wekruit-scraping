#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
RESEARCHER_ROOT = ROOT / "researcher"
if str(RESEARCHER_ROOT) not in sys.path:
    sys.path.insert(0, str(RESEARCHER_ROOT))

from pipeline.sourcing_client import DEFAULT_BATCH_SIZE, dry_run_upload, upload_source_records
from pipeline.sourcing_records import content_hash, raw_storage_path, safe_id, utc_now


def first_non_empty(*values: Any) -> str:
    for value in values:
        if isinstance(value, list):
            joined = "; ".join(str(item).strip() for item in value if str(item).strip())
            if joined:
                return joined
        elif value not in (None, "", [], {}):
            text = str(value).strip()
            if text:
                return text
    return ""


def compact(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


def load_input_records(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    if suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("records", "items", "projects", "candidates", "data"):
                value = payload.get(key)
                if isinstance(value, list):
                    return value
            return [payload]
    raise ValueError(f"Unsupported input file format: {path}")


def iter_domain_records(source: str, records: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for record in records:
        if source == "devpost":
            yield from devpost_records(record)
        elif source == "github":
            yield github_record(record)
        else:
            yield generic_record(record)


def devpost_records(project: dict[str, Any]) -> Iterable[dict[str, Any]]:
    project_name = first_non_empty(project.get("name"), project.get("project_name"))
    project_url = first_non_empty(project.get("project_url"), project.get("url"))
    yield {
        "entityType": "project",
        "sourceNativeId": first_non_empty(project_url, project_name),
        "sourceUrl": project_url,
        "display": compact({
            "title": project_name,
            "hackathon": project.get("hackathon"),
            "homepage": project_url,
        }),
        "rawSummary": compact({
            "winner": project.get("winner"),
            "likes": project.get("likes"),
            "github": project.get("github_links") or project.get("github_repos"),
            "demo": project.get("demo_links"),
            "tech": project.get("tech_tags") or project.get("tech_stack"),
        }),
        "raw": project,
    }

    for member in project.get("members", []) or []:
        if not isinstance(member, dict):
            continue
        member_name = first_non_empty(member.get("name"), member.get("member_name"))
        member_url = first_non_empty(member.get("devpost_profile"), member.get("member_devpost"))
        yield {
            "entityType": "person",
            "sourceNativeId": first_non_empty(member_url, member.get("github_url"), member_name),
            "sourceUrl": member_url,
            "displayName": member_name,
            "display": compact({
                "name": member_name,
                "homepage": member.get("website"),
                "github": member.get("github_url"),
                "linkedin": member.get("linkedin_url"),
            }),
            "rawSummary": compact({
                "devpost": member_url,
                "github": member.get("github_url"),
                "linkedin": member.get("linkedin_url"),
                "twitter": member.get("twitter_url"),
                "projectUrl": project_url,
                "projectName": project_name,
            }),
            "raw": {
                "member": member,
                "project": compact({
                    "name": project_name,
                    "url": project_url,
                    "hackathon": project.get("hackathon"),
                }),
            },
        }


def github_record(candidate: dict[str, Any]) -> dict[str, Any]:
    profile = candidate.get("profile") if isinstance(candidate.get("profile"), dict) else {}
    username = first_non_empty(candidate.get("username"), profile.get("login"))
    html_url = first_non_empty(profile.get("html_url"), f"https://github.com/{username}" if username else "")
    return {
        "entityType": "person",
        "sourceNativeId": username or html_url,
        "sourceUrl": html_url,
        "displayName": first_non_empty(profile.get("name"), username),
        "institution": profile.get("company"),
        "display": compact({
            "name": first_non_empty(profile.get("name"), username),
            "institution": profile.get("company"),
            "homepage": profile.get("blog"),
            "github": html_url,
        }),
        "rawSummary": compact({
            "email": first_non_empty(candidate.get("emails"), profile.get("email")),
            "github": html_url,
            "location": profile.get("location"),
            "followers": profile.get("followers"),
            "publicRepos": profile.get("public_repos"),
            "totalCommits": candidate.get("total_commits"),
            "score": candidate.get("score"),
        }),
        "raw": candidate,
    }


def generic_record(record: dict[str, Any]) -> dict[str, Any]:
    name = first_non_empty(
        record.get("name"),
        record.get("member_name"),
        record.get("username"),
        record.get("full_name"),
        record.get("project_name"),
    )
    institution = first_non_empty(record.get("institution"), record.get("company"), record.get("affiliation"))
    source_url = first_non_empty(
        record.get("github_url"),
        record.get("member_github"),
        record.get("html_url"),
        record.get("blog"),
        record.get("website"),
        record.get("member_website"),
        record.get("project_url"),
    )
    return {
        "entityType": first_non_empty(record.get("entityType"), record.get("entity_type"), record.get("type")) or "person",
        "sourceNativeId": first_non_empty(
            record.get("sourceNativeId"),
            record.get("source_native_id"),
            record.get("id"),
            record.get("username"),
            record.get("member_username"),
            record.get("member_devpost"),
            record.get("github_url"),
            record.get("member_github"),
            record.get("project_url"),
            record.get("email"),
        ),
        "sourceUrl": source_url,
        "displayName": name,
        "institution": institution,
        "display": compact({
            "name": name,
            "title": first_non_empty(record.get("title"), record.get("project_name")),
            "institution": institution,
            "homepage": first_non_empty(record.get("homepage"), record.get("website"), record.get("member_website"), record.get("blog")),
            "github": first_non_empty(record.get("github_url"), record.get("member_github"), record.get("html_url")),
            "linkedin": first_non_empty(record.get("linkedin_url"), record.get("member_linkedin")),
        }),
        "rawSummary": compact({
            "email": first_non_empty(record.get("email"), record.get("emails"), record.get("member_email")),
            "github": first_non_empty(record.get("github_url"), record.get("member_github"), record.get("html_url")),
            "linkedin": first_non_empty(record.get("linkedin_url"), record.get("member_linkedin")),
            "devpost": first_non_empty(record.get("member_devpost"), record.get("project_url")),
            "score": first_non_empty(record.get("score"), record.get("score_total")),
        }),
        "raw": record,
    }


def source_record_id(source: str, entity_type: str, native_id: str, raw: dict[str, Any]) -> str:
    stable = native_id or content_hash(raw).split(":", 1)[1][:16]
    return f"src_{safe_id(source)}_{safe_id(entity_type)}_{safe_id(stable)}"


def to_source_records(
    *,
    run_id: str,
    domain: str,
    source: str,
    records: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    now = utc_now()
    output: list[dict[str, Any]] = []
    for normalized in iter_domain_records(source, records):
        raw = normalized.get("raw") if isinstance(normalized.get("raw"), dict) else normalized
        entity_type = str(normalized.get("entityType") or "generic_record")
        native_id = first_non_empty(normalized.get("sourceNativeId"), normalized.get("sourceUrl"))
        record_id = source_record_id(source, entity_type, native_id, raw)
        output.append({
            "sourceRecordId": record_id,
            "runId": run_id,
            "domain": domain,
            "source": source,
            "entityType": entity_type,
            "sourceNativeId": native_id or record_id,
            "sourceUrl": normalized.get("sourceUrl"),
            "displayName": normalized.get("displayName"),
            "institution": normalized.get("institution"),
            "display": normalized.get("display") or {},
            "rawSummary": normalized.get("rawSummary") or {},
            "raw": raw,
            "rawStoragePath": raw_storage_path(
                domain=domain,
                source=source,
                run_id=run_id,
                source_record_id=record_id,
            ),
            "contentHash": content_hash(raw),
            "schemaVersion": "sourcing_source_record.v1",
            "createdAt": now,
            "updatedAt": now,
        })
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Upload Devpost, GitHub, researcher, or manual files to core-service sourcing API.")
    parser.add_argument("--input", required=True, type=Path, help="CSV, JSON, or JSONL file")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--domain", required=True, help="Example: researcher, developer, hackathon, manual")
    parser.add_argument("--source", required=True, help="Example: openalex, github, devpost, csv")
    parser.add_argument("--api-base-url", default="http://127.0.0.1:5100/api/sourcing")
    parser.add_argument("--output-root", default="data")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    raw_records = load_input_records(args.input)
    records = to_source_records(
        run_id=args.run_id,
        domain=args.domain,
        source=args.source,
        records=raw_records,
    )
    if not records:
        raise SystemExit(f"No records converted from {args.input}")

    if args.dry_run:
        result = dry_run_upload(
            data_root=args.output_root,
            run_id=args.run_id,
            domain=args.domain,
            records=records,
        )
        print(f"dry-run wrote {result.record_count} source records to {result.records_payload_path}")
        return 0

    result = upload_source_records(
        api_base_url=args.api_base_url,
        run_id=args.run_id,
        domain=args.domain,
        records=records,
        batch_size=args.batch_size,
    )
    print(f"uploaded {result.record_count} source records from {args.source} to {args.api_base_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
