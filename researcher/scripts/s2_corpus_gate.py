from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.corpus_gate import run_corpus_gate

try:
    from config.settings import DATA_ROOT  # type: ignore
except ModuleNotFoundError:
    DATA_ROOT = "data"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 6 corpus gate over staged OpenAlex runs; writes gated_works.jsonl and gate_decisions.jsonl")
    parser.add_argument("--input-run", required=True)
    parser.add_argument("--venue-table", default="data/assets/ai_cs_venue_tiers.csv")
    parser.add_argument("--output-root", default=DATA_ROOT)
    parser.add_argument("--run-id", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    run_corpus_gate(
        data_root=args.output_root,
        input_run_id=args.input_run,
        venue_table=args.venue_table,
        run_id=args.run_id,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
