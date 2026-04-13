from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.incremental_state import load_seen_ids, write_checkpoint, write_seen_ids
from pipeline.raw_staging import stage_records
from pipeline.run_context import SourceAttempt, create_run_context
from sources.crossref import CrossrefAdapter, normalize_doi

try:
    from config.settings import DATA_ROOT  # type: ignore
except ModuleNotFoundError:
    DATA_ROOT = "data"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 1 Crossref DOI backfill over staged OpenAlex works")
    parser.add_argument("--input-run", required=True)
    parser.add_argument("--output-root", default=DATA_ROOT)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--resume-lineage", action="store_true")
    return parser


def _resolve_run_id(run_id: str | None) -> str:
    if run_id:
        return run_id
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("run-%Y%m%d-%H%M%S")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _input_run_paths(data_root: Path | str, input_run: str) -> tuple[Path, Path]:
    data_root = Path(data_root)
    run_dir = data_root / "runs" / input_run
    manifest_path = run_dir / "run.json"
    works_path = run_dir / "openalex" / "works_raw.jsonl"
    return manifest_path, works_path


def run_crossref_backfill(args: argparse.Namespace) -> dict:
    manifest_path, works_path = _input_run_paths(args.output_root, args.input_run)
    if not manifest_path.exists() or not works_path.exists():
        raise SystemExit(f"Missing staged OpenAlex run: {args.input_run}")

    parent_manifest = _load_json(manifest_path)
    source_works = _load_jsonl(works_path)
    slice_definition = parent_manifest["slice"]

    ctx = create_run_context(
        data_root=args.output_root,
        run_id=_resolve_run_id(args.run_id),
        preset_type=slice_definition["type"],
        preset_value=slice_definition["value"],
        since_year=parent_manifest["since_year"],
        max_records=parent_manifest["limits"]["max_records"],
        max_pages=1,
        default_retry_limit=parent_manifest["retries"]["default_retry_limit"],
        source_name="crossref",
        sources_requested=("crossref",),
        parent_run_id=args.input_run,
    )
    ctx.initialize()

    adapter = CrossrefAdapter()
    seen_dois = load_seen_ids(args.output_root, lineage_key=args.input_run, source_id="crossref") if args.resume_lineage else set()
    skipped_no_doi = 0
    skipped_existing = 0
    staged_records: list[dict] = []
    last_doi: str | None = None

    for work_record in source_works:
        doi = normalize_doi((work_record.get("raw") or {}).get("doi"))
        if not doi:
            skipped_no_doi += 1
            continue
        if doi in seen_dois:
            skipped_existing += 1
            continue

        payload = adapter.fetch_work(doi)
        staged_records.append(
            adapter.build_work_record(
                run_id=ctx.run_id,
                doi=doi,
                slice_definition=slice_definition,
                payload=payload,
            )
        )
        seen_dois.add(doi)
        last_doi = doi

    if staged_records:
        stage_records(
            ctx.raw_path("crossref", "works_backfill_raw.jsonl"),
            staged_records,
            mirror_path=ctx.latest_raw_path("crossref", "works_backfill_raw.jsonl"),
        )

    write_seen_ids(args.output_root, lineage_key=args.input_run, source_id="crossref", values=seen_dois)
    write_checkpoint(
        args.output_root,
        lineage_key=args.input_run,
        source_id="crossref",
        payload={
            "input_run": args.input_run,
            "last_doi": last_doi,
            "processed_dois": sorted(seen_dois),
        },
    )

    ctx.record_source_attempt(
        "crossref",
        SourceAttempt(
            request_params={
                "input_run": args.input_run,
                "skipped_no_doi": skipped_no_doi,
                "skipped_existing": skipped_existing,
            },
            retry_count=0,
            checkpoint_cursor=last_doi,
            page_count=1,
            record_count=len(staged_records),
            error_summary="",
        ),
    )
    ctx.complete_source("crossref")
    return {
        "run_id": ctx.run_id,
        "records_staged": len(staged_records),
        "run_manifest": ctx.write_manifest(status="completed"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    run_crossref_backfill(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
