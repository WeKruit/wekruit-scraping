from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.sourcing_client import DEFAULT_BATCH_SIZE, dry_run_upload, upload_source_records
from pipeline.sourcing_records import collect_source_records

try:
    from config.settings import DATA_ROOT  # type: ignore
except ModuleNotFoundError:
    DATA_ROOT = "data"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert staged JSONL into sourcing sourceRecord payloads and upload them to core-service ingest",
    )
    parser.add_argument("--input-run", required=True, help="Run ID under data/runs/<run_id>")
    parser.add_argument("--output-root", default=DATA_ROOT, help="Local data root; default comes from config/settings.py or data")
    parser.add_argument("--domain", default="researcher")
    parser.add_argument("--api-base-url", default="http://127.0.0.1:5100/api/sourcing")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--dry-run", action="store_true", help="Write payload JSONL locally without network calls")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    records = collect_source_records(
        data_root=args.output_root,
        run_id=args.input_run,
        domain=args.domain,
    )
    if not records:
        raise SystemExit(f"No staged JSONL records found for input run: {args.input_run}")

    if args.dry_run:
        result = dry_run_upload(
            data_root=args.output_root,
            run_id=args.input_run,
            domain=args.domain,
            records=records,
        )
        print(
            f"dry-run wrote {result.record_count} source records "
            f"from {result.source_count} source(s) to {result.records_payload_path}"
        )
        return 0

    result = upload_source_records(
        api_base_url=args.api_base_url,
        run_id=args.input_run,
        domain=args.domain,
        records=records,
        batch_size=args.batch_size,
    )
    print(f"uploaded {result.record_count} source records from {result.source_count} source(s) to {args.api_base_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
