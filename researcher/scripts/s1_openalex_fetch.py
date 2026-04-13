from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.raw_staging import stage_records
from pipeline.run_context import SourceAttempt, create_run_context
from presets.ai_ml import get_preset, list_presets
from sources.openalex import OpenAlexAdapter

try:
    from config.settings import DATA_ROOT  # type: ignore
except ModuleNotFoundError:
    DATA_ROOT = "data"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 1 OpenAlex ingest for AI/ML presets")
    parser.add_argument("--preset-type", choices=("venue", "concept", "keyword"))
    parser.add_argument("--preset")
    parser.add_argument("--since", type=int)
    parser.add_argument("--max-records", type=int, default=1000)
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--output-root", default=DATA_ROOT)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--replay-run", default=None)
    return parser


def _resolve_run_id(run_id: str | None) -> str:
    if run_id:
        return run_id
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("run-%Y%m%d-%H%M%S")


def run_openalex_ingest(args: argparse.Namespace) -> dict[str, Any]:
    if not args.preset_type or not args.preset or args.since is None:
        raise SystemExit("--preset-type, --preset, and --since are required unless --replay-run is used")
    if args.preset not in list_presets(args.preset_type):
        raise SystemExit(f"Unknown preset {args.preset_type}/{args.preset}")
    preset = get_preset(args.preset_type, args.preset)
    run_id = _resolve_run_id(args.run_id)
    ctx = create_run_context(
        data_root=args.output_root,
        run_id=run_id,
        preset_type=args.preset_type,
        preset_value=preset["label"],
        since_year=args.since,
        max_records=args.max_records,
        max_pages=args.max_pages,
        source_name="openalex",
        sources_requested=("openalex",),
    )
    ctx.initialize()

    adapter = OpenAlexAdapter()
    query = adapter.build_query(
        preset,
        since_year=args.since,
        max_records=args.max_records,
        max_pages=args.max_pages,
    )

    seen_authors: dict[str, dict[str, Any]] = {}
    work_records: list[dict[str, Any]] = []
    author_records: list[dict[str, Any]] = []
    cursor = "*"
    page_number = 0

    while True:
        page = adapter.fetch_page(query, cursor=cursor)
        results = page.get("results", []) or []
        page_number += 1
        page_works, page_authors = adapter.parse_page(
            results,
            preset=preset,
            run_id=ctx.run_id,
            page_number=page_number,
            checkpoint_cursor=cursor,
            seen_authors=seen_authors,
        )
        work_records.extend(page_works)
        cursor = (page.get("meta") or {}).get("next_cursor")
        if page_works:
            stage_records(
                ctx.raw_path("openalex", "works_raw.jsonl"),
                page_works,
                mirror_path=ctx.latest_raw_path("openalex", "works_raw.jsonl"),
            )
        if page_authors:
            stage_records(
                ctx.raw_path("openalex", "authors_raw.jsonl"),
                page_authors,
                mirror_path=ctx.latest_raw_path("openalex", "authors_raw.jsonl"),
            )
        if not cursor:
            break
        if args.max_pages and page_number >= args.max_pages:
            break
        if args.max_records and len(work_records) >= args.max_records:
            break

    ctx.record_source_attempt(
        "openalex",
        SourceAttempt(
            request_params={
                "preset_type": args.preset_type,
                "preset": args.preset,
                "since": args.since,
            },
            retry_count=0,
            checkpoint_cursor=cursor,
            page_count=page_number,
            record_count=len(work_records),
            error_summary="",
        ),
    )
    ctx.complete_source("openalex")
    return {
        "run_id": ctx.run_id,
        "preset": preset,
        "works_count": len(work_records),
        "authors_count": len(seen_authors),
        "run_manifest": ctx.write_manifest(status="completed"),
    }


def replay_openalex_run(*, data_root: str | Path, run_id: str) -> dict[str, Any]:
    run_dir = Path(data_root) / "runs" / run_id
    manifest_path = run_dir / "run.json"
    works_path = run_dir / "openalex" / "works_raw.jsonl"
    authors_path = run_dir / "openalex" / "authors_raw.jsonl"
    if not manifest_path.exists() or not works_path.exists():
        raise SystemExit(f"Missing staged OpenAlex run: {run_id}")
    if not authors_path.exists():
        authors_path.parent.mkdir(parents=True, exist_ok=True)
        authors_path.touch()
    return {
        "run_id": run_id,
        "run_manifest": json.loads(manifest_path.read_text(encoding="utf-8")),
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.replay_run:
        replay_openalex_run(data_root=args.output_root, run_id=args.replay_run)
        return 0
    run_openalex_ingest(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
