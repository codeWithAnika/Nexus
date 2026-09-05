from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

from sqlalchemy import func, select

from app.database.connection import SessionLocal
from app.dataset_ingestion.config import DEFAULT_ARCHIVE_PATH, DEFAULT_DATASET_ROOT
from app.entity_extraction.config import PILOT_IMAGE_IDS, VALIDATION_BATCH_IMAGE_IDS
from app.entity_extraction.extractor import PilotScopeError, extract_batch_entities
from app.entity_resolution.models import (
    CandidateResolution,
    PilotResolutionReport,
    ResolutionDecision,
)
from app.entity_resolution.resolver import ConservativeEntityResolver
from app.entity_resolution.service import (
    CaseOwnershipMismatchError,
    resolve_and_persist_validation_batch,
)
from app.models.alert import Alert
from app.models.analysis import Analysis
from app.models.entity import Entity, EntityMentionProvenance, EntityType
from app.models.entity_identifier import EntityIdentifier
from app.models.evidence import Evidence
from app.models.fir import FIR
from app.models.relationship import Relationship


class EntityResolutionBatch25Tests(unittest.TestCase):
    """Comprehensive test suite for the 25-FIR controlled validation batch (Image IDs 0–24).

    Covers all 20 required acceptance and verification criteria.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.db = SessionLocal()
        cls.handoff, cls.ext_report = extract_batch_entities(
            db=cls.db, requested_image_ids=set(VALIDATION_BATCH_IMAGE_IDS)
        )
        cls.report1 = resolve_and_persist_validation_batch(db=cls.db, handoff=cls.handoff)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db.close()

    # 1. 25-FIR scope
    def test_01_twenty_five_firs_scope(self) -> None:
        self.assertEqual(self.ext_report.total_images_processed, 25)
        self.assertEqual(set(self.report1.pilot_image_ids), set(range(25)))
        # Guard: IDs outside 0..24 rejected
        with self.assertRaises(PilotScopeError):
            extract_batch_entities(db=self.db, requested_image_ids={25})
        with self.assertRaises(PilotScopeError):
            extract_batch_entities(db=self.db, requested_image_ids={0, 100})

    # 2. Extraction candidate count
    def test_02_extraction_candidate_count(self) -> None:
        # Exactly 84 extraction candidates produced across images 0–24
        self.assertEqual(len(self.handoff["entities"]), 84)
        self.assertEqual(self.report1.total_candidates_processed, 84)
        self.assertEqual(self.ext_report.ocr_records_processed, 101)

    # 3. Same-FIR PERSON matching
    def test_03_same_fir_person_matching(self) -> None:
        # In Image 3, Rubina Laskar appears twice within the same FIR
        same_fir_persons = [
            r for r in self.report1.resolutions
            if r.decision == ResolutionDecision.MATCHED_EXISTING_SAME_FIR and r.entity_type == "PERSON"
        ]
        self.assertGreaterEqual(len(same_fir_persons), 1)
        # Verify both Rubina mentions share the same canonical entity ID
        rubina = [r for r in self.report1.resolutions if r.normalized_value == "Rubina Laskar"]
        self.assertEqual(len(rubina), 2)
        self.assertEqual(rubina[0].canonical_entity_id, rubina[1].canonical_entity_id)

    # 4. Cross-FIR PERSON separation (KEPT_SEPARATE_CROSS_FIR)
    def test_04_cross_fir_person_separation(self) -> None:
        cross_fir_persons = [
            r for r in self.report1.resolutions
            if r.decision == ResolutionDecision.KEPT_SEPARATE_CROSS_FIR
        ]
        # Persons with identical normalized names across different FIRs must be kept separate
        self.assertGreaterEqual(len(cross_fir_persons), 1)
        self.assertEqual(self.report1.cross_fir_person_matches_prevented, len(cross_fir_persons))

        # Check Si Sahabuddin Mondal across different FIRs
        sahabuddin = [r for r in self.report1.resolutions if r.normalized_value == "Sahabuddin Mondal"]
        if len(sahabuddin) > 1:
            fir_ids = {r.fir_id for r in sahabuddin}
            entity_ids = {r.canonical_entity_id for r in sahabuddin}
            # Different FIRs must map to different canonical entity IDs
            self.assertEqual(len(fir_ids), len(entity_ids))

    # 5. Cross-FIR POLICE_STATION matching
    def test_05_cross_fir_police_station_matching(self) -> None:
        cross_fir_stations = [
            r for r in self.report1.resolutions
            if r.decision == ResolutionDecision.MATCHED_EXISTING_CROSS_FIR and r.entity_type == "POLICE_STATION"
        ]
        self.assertGreater(len(cross_fir_stations), 10)
        # All Airport Police Station mentions must share a single canonical entity ID
        airport_mentions = [r for r in self.report1.resolutions if r.normalized_value == "Airport Police Station"]
        self.assertGreaterEqual(len(airport_mentions), 25)
        canonical_ids = {r.canonical_entity_id for r in airport_mentions}
        self.assertEqual(len(canonical_ids), 1, "Airport Police Station must canonicalize to exactly 1 entity")

    # 6. Cross-FIR STATUTE matching
    def test_06_cross_fir_statute_matching(self) -> None:
        statute_res = [r for r in self.report1.resolutions if r.entity_type == "STATUTE"]
        self.assertEqual(len(statute_res), 19)
        # Identical statute occurrences in different FIRs merge cleanly
        batch_statute_ids = {r.canonical_entity_id for r in statute_res}
        statute_entities = self.db.scalars(
            select(Entity).where(Entity.id.in_(batch_statute_ids), Entity.entity_type == EntityType.STATUTE)
        ).all()
        self.assertLessEqual(len(statute_entities), 19)
        self.assertEqual(len(statute_entities), len(batch_statute_ids))

    # 7. Type isolation
    def test_07_type_isolation(self) -> None:
        resolver = ConservativeEntityResolver()
        cand_p = {
            "temp_id": "p1", "case_id": 1, "fir_id": 10, "dataset_image_id": 0,
            "source_evidence_id": 100, "extraction_entity_type": "PERSON",
            "raw_value": "Airport", "normalized_value": "Airport",
        }
        cand_s = {
            "temp_id": "s1", "case_id": 1, "fir_id": 10, "dataset_image_id": 0,
            "source_evidence_id": 100, "extraction_entity_type": "POLICE_STATION",
            "raw_value": "Airport", "normalized_value": "Airport",
        }
        res_p = resolver.resolve_candidate(cand_p)
        res_s = resolver.resolve_candidate(cand_s)
        self.assertNotEqual(res_p.entity_type, res_s.entity_type)
        self.assertEqual(res_p.decision, ResolutionDecision.CREATED_NEW)
        self.assertEqual(res_s.decision, ResolutionDecision.CREATED_NEW)

    # 8. Duplicate mention preservation
    def test_08_duplicate_mention_preservation(self) -> None:
        airport_mentions = [r for r in self.report1.resolutions if r.normalized_value == "Airport Police Station"]
        station_ent_id = airport_mentions[0].canonical_entity_id
        # In database, station_ent_id must have multiple distinct EntityMentionProvenance records for this batch
        batch_ev_ids = {c["source_evidence_id"] for c in self.handoff["entities"]}
        provs = self.db.scalars(
            select(EntityMentionProvenance).where(
                EntityMentionProvenance.entity_id == station_ent_id,
                EntityMentionProvenance.evidence_id.in_(batch_ev_ids),
            )
        ).all()
        self.assertEqual(len(provs), len(airport_mentions))

    # 9. Provenance completeness
    def test_09_provenance_completeness(self) -> None:
        self.assertEqual(self.report1.provenance_rows_total, 84)
        batch_ev_ids = {c["source_evidence_id"] for c in self.handoff["entities"]}
        total_in_db = self.db.scalar(
            select(func.count(EntityMentionProvenance.id)).where(
                EntityMentionProvenance.evidence_id.in_(batch_ev_ids)
            )
        )
        self.assertEqual(total_in_db, 84)

    # 10. Evidence ownership
    def test_10_evidence_ownership(self) -> None:
        for r in self.report1.resolutions:
            evi = self.db.get(Evidence, r.source_evidence_id)
            self.assertIsNotNone(evi)
            self.assertEqual(evi.case_id, r.case_id)
            self.assertEqual(evi.fir_id, r.fir_id)

    # 11. Case ownership
    def test_11_case_ownership(self) -> None:
        for r in self.report1.resolutions:
            ent = self.db.get(Entity, r.canonical_entity_id)
            self.assertIsNotNone(ent)
            self.assertEqual(ent.case_id, r.case_id)

    # 12. Identifier handling
    def test_12_zero_entity_identifiers(self) -> None:
        self.assertEqual(self.report1.identifiers_created, 0)
        ident_count = self.db.scalar(select(func.count(EntityIdentifier.id)))
        self.assertEqual(ident_count, 0)

    # 13. Zero relationships
    def test_13_zero_relationships(self) -> None:
        self.assertEqual(self.report1.relationships_count, 0)

    # 14. Zero analysis
    def test_14_zero_analysis(self) -> None:
        self.assertEqual(self.report1.analyses_count, 0)

    # 15. Zero alerts
    def test_15_zero_alerts(self) -> None:
        self.assertEqual(self.report1.alerts_count, 0)

    # 16. Idempotent rerun
    def test_16_idempotent_rerun(self) -> None:
        report2 = resolve_and_persist_validation_batch(db=self.db, handoff=self.handoff)
        self.assertEqual(report2.canonical_entities_created, 0)
        self.assertEqual(report2.canonical_entities_reused, self.report1.canonical_entities_total)
        self.assertEqual(report2.provenance_rows_created, 0)
        self.assertEqual(report2.provenance_rows_reused, 84)
        self.assertTrue(report2.is_idempotent_rerun)

    # 17. Rollback verification
    def test_17_transactional_rollback(self) -> None:
        ent_count_before = self.db.scalar(select(func.count(Entity.id)))
        prov_count_before = self.db.scalar(select(func.count(EntityMentionProvenance.id)))

        bad_handoff = {
            "entities": [
                {
                    "temp_id": "bad_cand",
                    "case_id": 21,
                    "fir_id": 575,
                    "dataset_image_id": 0,
                    "source_evidence_id": 9999999,  # non-existent
                    "extraction_entity_type": "PERSON",
                    "raw_value": "Bad Candidate",
                    "normalized_value": "Bad Candidate",
                    "provenance": self.handoff["entities"][0]["provenance"],
                }
            ],
            "relationships": [],
            "metadata": self.handoff["metadata"],
        }
        with self.assertRaises(CaseOwnershipMismatchError):
            resolve_and_persist_validation_batch(db=self.db, handoff=bad_handoff)

        self.assertEqual(self.db.scalar(select(func.count(Entity.id))), ent_count_before)
        self.assertEqual(self.db.scalar(select(func.count(EntityMentionProvenance.id))), prov_count_before)

    # 18. Oracle compatibility
    def test_18_oracle_compatibility(self) -> None:
        batch_ent_ids = {r.canonical_entity_id for r in self.report1.resolutions}
        entities = self.db.scalars(select(Entity).where(Entity.id.in_(batch_ent_ids))).all()
        self.assertEqual(len(entities), self.report1.canonical_entities_total)
        for e in entities:
            self.assertIn(e.entity_type, {EntityType.PERSON, EntityType.POLICE_STATION, EntityType.STATUTE})

    # 19. Raw dataset hash preservation
    def test_19_raw_dataset_hashes_preserved(self) -> None:
        json_path = DEFAULT_DATASET_ROOT / "FIR_details.json"
        self.assertTrue(json_path.exists())
        h_json = hashlib.sha256(json_path.read_bytes()).hexdigest()
        self.assertEqual(h_json, "693a1e11bd116e2458898e43c48785853b6d6e99439f315b761063c0bb2a357a")

        self.assertTrue(DEFAULT_ARCHIVE_PATH.exists())
        h_zip = hashlib.sha256(DEFAULT_ARCHIVE_PATH.read_bytes()).hexdigest()
        self.assertEqual(h_zip, "be2026f8355a9cb051b42cc975b635fe56a2f261ba5b60aa4ad7b1de5cf5561b")

    # 20. Existing 544 FIR/Evidence preservation
    def test_20_fir_and_evidence_counts_preserved(self) -> None:
        fir_count = self.db.scalar(select(func.count(FIR.id)))
        ev_count = self.db.scalar(select(func.count(Evidence.id)))
        self.assertEqual(fir_count, 544)
        self.assertEqual(ev_count, 544)


if __name__ == "__main__":
    unittest.main()
