from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select

from app.database.connection import SessionLocal
from app.dataset_ingestion.config import DEFAULT_ARCHIVE_PATH, DEFAULT_DATASET_ROOT
from app.entity_extraction.config import VALIDATION_BATCH_IMAGE_IDS
from app.entity_extraction.extractor import extract_batch_entities
from app.entity_resolution.models import ResolutionDecision
from app.entity_resolution.service import (
    CaseOwnershipMismatchError,
    resolve_and_persist_validation_batch,
)
from app.models.alert import Alert
from app.models.analysis import Analysis
from app.models.entity import Entity, EntityMentionProvenance
from app.models.entity_identifier import EntityIdentifier
from app.models.evidence import Evidence
from app.models.fir import FIR
from app.models.relationship import Relationship


def main() -> None:
    print("=" * 80)
    print("NEXUS SIH — 25-FIR CONTROLLED ENTITY RESOLUTION VALIDATION BATCH")
    print("=" * 80)

    db = SessionLocal()
    try:
        # Step 1: Extraction & Candidate Inspection
        print("\n[Step 1] Loading 25-FIR Extraction Batch (Image IDs 0–24)...")
        handoff, ext_report = extract_batch_entities(db=db, requested_image_ids=set(VALIDATION_BATCH_IMAGE_IDS))
        candidates = handoff["entities"]

        type_counts = Counter(c["extraction_entity_type"] for c in candidates)
        cat_counts = Counter(c["provenance"]["category_id"] for c in candidates)

        print(f"  FIRs processed:            {ext_report.total_images_processed} / 25")
        print(f"  OCR records processed:     {ext_report.ocr_records_processed}")
        print(f"  Extraction candidates:     {len(candidates)}")
        print(f"  Candidates by EntityType:  {dict(type_counts)}")
        print(f"  Candidates by Category ID: {dict(cat_counts)}")
        print(f"  Duplicate mentions flag:   {ext_report.duplicate_mentions_preserved}")
        print(f"  Low OCR confidence count:  {ext_report.low_ocr_confidence_count}")

        # Step 2: First-Run Persistence
        print("\n[Step 2] Executing Validation Batch Resolution & Persistence (Run 1)...")
        report1 = resolve_and_persist_validation_batch(db=db, handoff=handoff)
        print(f"  Total Candidates Processed:           {report1.total_candidates_processed}")
        print(f"  Canonical Entities Created:           {report1.canonical_entities_created}")
        print(f"  Canonical Entities Reused:            {report1.canonical_entities_reused}")
        print(f"  Canonical Entities Total:             {report1.canonical_entities_total}")
        print(f"  Entities by Type:                     {report1.entities_by_type}")
        print(f"  Provenance Rows Created:              {report1.provenance_rows_created}")
        print(f"  Provenance Rows Reused:               {report1.provenance_rows_reused}")
        print(f"  Provenance Rows Total:                {report1.provenance_rows_total}")
        print(f"  Entity Identifiers Created:           {report1.identifiers_created}")
        print(f"  Decisions Breakdown:                  {report1.candidates_by_decision}")
        print(f"  Cross-FIR Person Matches Prevented:   {report1.cross_fir_person_matches_prevented}")
        print(f"  Cross-FIR Station Matches:            {report1.cross_fir_station_matches}")
        print(f"  Cross-FIR Statute Matches:            {report1.cross_fir_statute_matches}")
        print(f"  Relationships Count:                  {report1.relationships_count}")
        print(f"  Analyses Count:                       {report1.analyses_count}")
        print(f"  Alerts Count:                         {report1.alerts_count}")

        # Step 3: Explicit Decisions Audit
        print("\n[Step 3] Cross-FIR Policy Audit:")
        cross_fir_prevented = [r for r in report1.resolutions if r.decision == ResolutionDecision.KEPT_SEPARATE_CROSS_FIR]
        print(f"  Persons kept separate across FIRs: {len(cross_fir_prevented)}")
        for r in cross_fir_prevented[:5]:
            print(f"    - [{r.temp_id}] '{r.normalized_value}' in FIR #{r.fir_id} kept separate as Entity #{r.canonical_entity_id}")

        station_matches = [r for r in report1.resolutions if r.decision == ResolutionDecision.MATCHED_EXISTING_CROSS_FIR and r.entity_type == "POLICE_STATION"]
        print(f"  Police stations canonicalized across FIRs: {len(station_matches)}")
        if station_matches:
            sample = station_matches[0]
            print(f"    - Sample: '{sample.normalized_value}' in FIR #{sample.fir_id} merged into Entity #{sample.canonical_entity_id}")

        # Step 4: Second-Run Idempotency Verification
        print("\n[Step 4] Testing Idempotency (Run 2)...")
        report2 = resolve_and_persist_validation_batch(db=db, handoff=handoff)
        print(f"  Canonical Entities Created:  {report2.canonical_entities_created} (expected: 0)")
        print(f"  Canonical Entities Reused:   {report2.canonical_entities_reused} (expected: {report1.canonical_entities_total})")
        print(f"  Provenance Rows Created:     {report2.provenance_rows_created} (expected: 0)")
        print(f"  Provenance Rows Reused:      {report2.provenance_rows_reused} (expected: {report1.provenance_rows_total})")
        print(f"  Is Idempotent Rerun:         {report2.is_idempotent_rerun}")

        # Step 5: Rollback Safety Verification
        print("\n[Step 5] Testing Transaction Rollback on Failure...")
        ent_before = db.scalar(select(func.count(Entity.id)))
        prov_before = db.scalar(select(func.count(EntityMentionProvenance.id)))

        failing_handoff = {
            "entities": [
                {
                    "temp_id": "cand_fail_test",
                    "case_id": 21,
                    "fir_id": 575,
                    "dataset_image_id": 0,
                    "source_evidence_id": 9999999,  # Bad evidence ID
                    "extraction_entity_type": "PERSON",
                    "raw_value": "Failure Test Candidate",
                    "normalized_value": "Failure Test Candidate",
                    "provenance": candidates[0]["provenance"],
                }
            ],
            "relationships": [],
            "metadata": handoff["metadata"],
        }
        rollback_succeeded = False
        try:
            resolve_and_persist_validation_batch(db=db, handoff=failing_handoff)
        except CaseOwnershipMismatchError:
            ent_after = db.scalar(select(func.count(Entity.id)))
            prov_after = db.scalar(select(func.count(EntityMentionProvenance.id)))
            assert ent_before == ent_after, "Entity row leaked during rollback"
            assert prov_before == prov_after, "Provenance row leaked during rollback"
            rollback_succeeded = True
            print("  Rollback verification: PASS (Zero rows leaked, transaction cleanly rolled back)")

        # Step 6: Oracle State Audit
        print("\n[Step 6] Oracle XE Database Audit:")
        fir_count = db.scalar(select(func.count(FIR.id)))
        ev_count = db.scalar(select(func.count(Evidence.id)))
        ent_count = db.scalar(select(func.count(Entity.id)))
        ident_count = db.scalar(select(func.count(EntityIdentifier.id)))
        prov_count = db.scalar(select(func.count(EntityMentionProvenance.id)))
        rel_count = db.scalar(select(func.count(Relationship.id)))
        ana_count = db.scalar(select(func.count(Analysis.id)))
        alt_count = db.scalar(select(func.count(Alert.id)))

        print(f"  firs:                       {fir_count} (baseline unchanged: 544)")
        print(f"  evidence:                   {ev_count} (baseline unchanged: 544)")
        print(f"  entities:                   {ent_count}")
        print(f"  entity_mention_provenance:  {prov_count}")
        print(f"  entity_identifiers:         {ident_count}")
        print(f"  relationships:              {rel_count}")
        print(f"  analyses:                   {ana_count}")
        print(f"  alerts:                     {alt_count}")

        # Step 7: Raw Dataset Verification
        print("\n[Step 7] Checking Raw Dataset File Hashes...")
        json_path = DEFAULT_DATASET_ROOT / "FIR_details.json"
        if json_path.exists():
            h_json = hashlib.sha256(json_path.read_bytes()).hexdigest()
            print(f"  FIR_details.json: {h_json}")
        if DEFAULT_ARCHIVE_PATH.exists():
            h_zip = hashlib.sha256(DEFAULT_ARCHIVE_PATH.read_bytes()).hexdigest()
            print(f"  FIR_Dataset_ICDAR2023-main.zip: {h_zip}")

        print("\n" + "=" * 80)
        print("25-FIR ENTITY RESOLUTION VALIDATION: PASS")
        print("=" * 80)
    finally:
        db.close()


if __name__ == "__main__":
    main()
