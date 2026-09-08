from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.dataset_ingestion.config import DEFAULT_ARCHIVE_PATH, DEFAULT_DATASET_ROOT
from app.dataset_ingestion.handoff import write_handoff
from app.dataset_ingestion.importer import run_import
from app.dataset_ingestion.reporting import report_json


def validate_handoff_output_path(output_path: Path, dataset_root: Path) -> Path:
    resolved_output = output_path.expanduser().resolve()
    resolved_dataset = dataset_root.expanduser().resolve()
    if resolved_output == resolved_dataset or resolved_dataset in resolved_output.parents:
        raise ValueError("--handoff-output must be outside dataset_root")
    return resolved_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight or import the FIR dataset")
    parser.add_argument("--case-id", required=True, type=int, help="Existing Case ID")
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE_PATH)
    parser.add_argument("--dry-run", action="store_true", help="Parse and report without database or storage writes")
    parser.add_argument("--execute", action="store_true", help="Enable database and storage writes")
    parser.add_argument("--inspect-db", action="store_true", help="Inspect existing identities during dry-run")
    parser.add_argument("--handoff-output", type=Path)
    args = parser.parse_args()
    if args.dry_run and args.execute:
        parser.error("--dry-run and --execute cannot be used together")
    if args.handoff_output:
        try:
            args.handoff_output = validate_handoff_output_path(args.handoff_output, args.dataset_root)
        except ValueError as exc:
            parser.error(str(exc))

    db = None
    if args.execute or args.inspect_db:
        from app.database.connection import SessionLocal

        db = SessionLocal()
    try:
        report = run_import(
            dataset_root=args.dataset_root,
            archive_path=args.archive,
            case_id=args.case_id,
            db=db,
            execute=args.execute,
            inspect_db=args.inspect_db,
        )
        if args.handoff_output:
            write_handoff(report.handoff, args.handoff_output)
        print(report_json(report))
        if report.handoff:
            print("HANDOFF_JSONL")
            print("".join(json.dumps(record.__dict__, ensure_ascii=True) + "\n" for record in report.handoff), end="")
        return 0 if report.failed == 0 and report.conflicts == 0 else 2
    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    raise SystemExit(main())
