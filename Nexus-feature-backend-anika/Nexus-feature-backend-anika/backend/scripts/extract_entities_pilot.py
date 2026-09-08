from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.connection import SessionLocal
from app.entity_extraction.extractor import extract_pilot_entities, PilotScopeError


def main() -> int:
    parser = argparse.ArgumentParser(description="Nexus SIH 5-FIR Entity Extraction Pilot")
    parser.add_argument("--output", type=Path, help="Path to write the JSON handoff output")
    parser.add_argument("--audit-output", type=Path, help="Path to write the JSON audit report")
    parser.add_argument("--verbose", action="store_true", help="Print candidates details")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        handoff, report = extract_pilot_entities(db=db)
    except PilotScopeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(handoff, indent=2, ensure_ascii=True), encoding="utf-8")
        print(f"Handoff JSON written to: {args.output}")

    if args.audit_output:
        args.audit_output.parent.mkdir(parents=True, exist_ok=True)
        args.audit_output.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=True), encoding="utf-8")
        print(f"Audit report written to: {args.audit_output}")

    print("\n=== 5-FIR ENTITY EXTRACTION PILOT AUDIT REPORT ===")
    print(f"Pilot Image IDs: {report.pilot_image_ids}")
    print(f"Total Images Processed: {report.total_images_processed}")
    print(f"OCR Records Processed: {report.ocr_records_processed}")
    print(f"Total Candidates Extracted: {report.candidates_extracted}")
    print(f"Candidates by Extraction Entity Type: {report.candidates_by_type}")
    print(f"Candidates by Source Category: {report.candidates_by_category}")
    print(f"Low OCR Confidence Count (< 0.60): {report.low_ocr_confidence_count}")
    print(f"Duplicate Mentions Preserved: {report.duplicate_mentions_preserved}")
    print(f"Unsupported DB Taxonomy Count (HANDOFF_ONLY): {report.unsupported_db_taxonomy_count}")
    print(f"Relationships Count: {report.relationships_count} (must be 0)")
    print(f"Entity Resolution Performed: {report.entity_resolution_performed} (must be False)")
    print(f"Database Migrations Created: {report.database_migrations_created} (must be False)")
    print(f"Raw Dataset Modified: {report.raw_dataset_modified} (must be False)")

    if args.verbose or not args.output:
        print("\n=== EXTRACTED CANDIDATES ===")
        for cand in handoff["entities"]:
            print(f"[{cand['temp_id']}] Image {cand['dataset_image_id']} | Type: {cand['extraction_entity_type']} | Raw: {repr(cand['raw_value'])} | Norm: {repr(cand['normalized_value'])}")
            print(f"     Confidence: OCR={cand['ocr_confidence']:.4f}, Ext={cand['extraction_confidence']:.4f}, Final={cand['entity_confidence']:.4f} (Low OCR: {cand['low_ocr_confidence']})")
            print(f"     Provenance: source_index={cand['provenance']['source_index']}, bbox={cand['provenance']['bbox']}, span=[{cand['provenance']['span']['start_char']}:{cand['provenance']['span']['end_char']}] matched={repr(cand['provenance']['span']['matched_text'])}")
            if cand['identifiers']:
                print(f"     Identifiers: {[ident['normalized_value'] for ident in cand['identifiers']]}")

    if report.rejections:
        print("\n=== REJECTIONS ===")
        for rej in report.rejections:
            print(f"  REJECTED: {rej}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
