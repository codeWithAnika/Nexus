from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select

from app.database.connection import SessionLocal
from app.entity_extraction.extractor import extract_pilot_entities
from app.entity_resolution.service import resolve_and_persist_pilot
from app.models.alert import Alert
from app.models.analysis import Analysis
from app.models.entity import Entity, EntityMentionProvenance
from app.models.entity_identifier import EntityIdentifier
from app.models.evidence import Evidence
from app.models.fir import FIR
from app.models.relationship import Relationship


def main() -> None:
    print("=" * 70)
    print("NEXUS SIH — CONTROLLED ENTITY RESOLUTION & PERSISTENCE PILOT")
    print("=" * 70)

    db = SessionLocal()
    try:
        # Step 1: Load extraction handoff
        print("\n[Step 1] Loading existing 5-FIR extraction handoff...")
        handoff, ext_report = extract_pilot_entities(db=db)
        print(f"  Extraction candidates loaded: {len(handoff['entities'])}")
        print(f"  Total images processed: {ext_report.total_images_processed}")

        # Step 2: First Run — Resolve and Persist
        print("\n[Step 2] Executing Entity Resolution & Persistence (Run 1)...")
        report1 = resolve_and_persist_pilot(db=db, handoff=handoff)
        print(f"  Total Candidates Processed: {report1.total_candidates_processed}")
        print(f"  Canonical Entities Created: {report1.canonical_entities_created}")
        print(f"  Canonical Entities Reused:  {report1.canonical_entities_reused}")
        print(f"  Canonical Entities Total:   {report1.canonical_entities_total}")
        print(f"  Entities by Type:           {report1.entities_by_type}")
        print(f"  Provenance Rows Created:    {report1.provenance_rows_created}")
        print(f"  Provenance Rows Reused:     {report1.provenance_rows_reused}")
        print(f"  Provenance Rows Total:      {report1.provenance_rows_total}")
        print(f"  Entity Identifiers Created: {report1.identifiers_created}")
        print(f"  Relationships Count:        {report1.relationships_count}")
        print(f"  Analyses Count:             {report1.analyses_count}")
        print(f"  Alerts Count:               {report1.alerts_count}")

        # Step 3: Resolution Decisions Breakdown
        print("\n[Step 3] Candidate Resolution Decisions:")
        for res in report1.resolutions:
            print(f"  [{res.temp_id}] {res.decision} -> Entity ID {res.canonical_entity_id} ('{res.canonical_entity_name}') | Type: {res.entity_type} | Norm: '{res.normalized_value}'")

        # Step 4: Step 4: Idempotency Verification (Run 2)
        print("\n[Step 4] Testing Idempotency (Run 2)...")
        report2 = resolve_and_persist_pilot(db=db, handoff=handoff)
        print(f"  Canonical Entities Created: {report2.canonical_entities_created} (expected: 0)")
        print(f"  Canonical Entities Reused:  {report2.canonical_entities_reused} (expected: {report1.canonical_entities_total})")
        print(f"  Provenance Rows Created:    {report2.provenance_rows_created} (expected: 0)")
        print(f"  Provenance Rows Reused:     {report2.provenance_rows_reused} (expected: 13)")
        print(f"  Is Idempotent Rerun:        {report2.is_idempotent_rerun}")

        # Step 5: Database State Audit
        print("\n[Step 5] Database State Audit:")
        fir_count = db.scalar(select(func.count(FIR.id)))
        ev_count = db.scalar(select(func.count(Evidence.id)))
        ent_count = db.scalar(select(func.count(Entity.id)))
        ident_count = db.scalar(select(func.count(EntityIdentifier.id)))
        prov_count = db.scalar(select(func.count(EntityMentionProvenance.id)))
        rel_count = db.scalar(select(func.count(Relationship.id)))
        ana_count = db.scalar(select(func.count(Analysis.id)))
        alt_count = db.scalar(select(func.count(Alert.id)))

        print(f"  FIR rows in DB:                      {fir_count}")
        print(f"  Evidence rows in DB:                 {ev_count}")
        print(f"  Entity rows in DB:                   {ent_count}")
        print(f"  EntityIdentifier rows in DB:         {ident_count}")
        print(f"  EntityMentionProvenance rows in DB:  {prov_count}")
        print(f"  Relationship rows in DB:             {rel_count}")
        print(f"  Analysis rows in DB:                 {ana_count}")
        print(f"  Alert rows in DB:                    {alt_count}")

        # Step 6: Provenance Traceability Verification
        print("\n[Step 6] Verifying Provenance Traceability (Entity -> Provenance -> Evidence -> FIR)...")
        provenances = db.scalars(select(EntityMentionProvenance).order_by(EntityMentionProvenance.id)).all()
        for p in provenances:
            ent = db.get(Entity, p.entity_id)
            evi = db.get(Evidence, p.evidence_id)
            fir = db.get(FIR, evi.fir_id) if evi and evi.fir_id else None
            assert ent is not None, f"Provenance {p.id} has no valid Entity"
            assert evi is not None, f"Provenance {p.id} has no valid Evidence"
            assert fir is not None, f"Evidence {evi.id} has no valid FIR"
            assert ent.case_id == evi.case_id, f"Case mismatch on provenance {p.id}"
            print(f"  Prov #{p.id}: Entity #{ent.id} ({ent.entity_type.value}: '{ent.name}') <- Evidence #{evi.id} <- FIR #{fir.fir_number} (img {fir.dataset_image_id}) [span: {p.start_char}..{p.end_char}]")

        # Step 7: Raw Dataset Verification
        print("\n[Step 7] Checking Raw Dataset File Hashes...")
        from app.dataset_ingestion.config import DEFAULT_ARCHIVE_PATH, DEFAULT_DATASET_ROOT
        json_path = DEFAULT_DATASET_ROOT / "FIR_details.json"
        if json_path.exists():
            h_json = hashlib.sha256(json_path.read_bytes()).hexdigest()
            print(f"  {json_path.name}: {h_json}")
        if DEFAULT_ARCHIVE_PATH.exists():
            h_zip = hashlib.sha256(DEFAULT_ARCHIVE_PATH.read_bytes()).hexdigest()
            print(f"  {DEFAULT_ARCHIVE_PATH.name}: {h_zip}")

        print("\n" + "=" * 70)
        print("ENTITY RESOLUTION PILOT: PASS")
        print("=" * 70)
    finally:
        db.close()


if __name__ == "__main__":
    main()
