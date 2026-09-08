from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

from sqlalchemy import func, select

from app.database.connection import SessionLocal
from app.entity_extraction.config import DEFAULT_CONFIG, PILOT_IMAGE_IDS
from app.entity_extraction.extractor import extract_pilot_entities
from app.entity_resolution.models import (
    CandidateResolution,
    PilotResolutionReport,
    ResolutionDecision,
)
from app.entity_resolution.resolver import ConservativeEntityResolver
from app.entity_resolution.service import (
    CaseOwnershipMismatchError,
    PilotScopeError,
    resolve_and_persist_pilot,
)
from app.models.alert import Alert
from app.models.analysis import Analysis
from app.models.entity import Entity, EntityMentionProvenance, EntityType
from app.models.entity_identifier import EntityIdentifier
from app.models.evidence import Evidence
from app.models.fir import FIR
from app.models.relationship import Relationship


class EntityResolutionPilotUnitTests(unittest.TestCase):
    """Pure in-memory unit tests for resolution engine logic."""

    def setUp(self) -> None:
        self.resolver = ConservativeEntityResolver()

    def test_conservative_resolver_type_isolation(self) -> None:
        # PERSON and POLICE_STATION with same normalized text must NEVER merge
        cand1 = {
            "temp_id": "c1",
            "case_id": 1,
            "fir_id": 10,
            "dataset_image_id": 0,
            "source_evidence_id": 100,
            "extraction_entity_type": "PERSON",
            "raw_value": "Airport",
            "normalized_value": "Airport",
        }
        cand2 = {
            "temp_id": "c2",
            "case_id": 1,
            "fir_id": 10,
            "dataset_image_id": 0,
            "source_evidence_id": 100,
            "extraction_entity_type": "POLICE_STATION",
            "raw_value": "Airport",
            "normalized_value": "Airport",
        }
        res1 = self.resolver.resolve_candidate(cand1)
        res2 = self.resolver.resolve_candidate(cand2)

        self.assertEqual(res1.decision, ResolutionDecision.CREATED_NEW)
        self.assertEqual(res2.decision, ResolutionDecision.CREATED_NEW)
        self.assertEqual(res1.entity_type, "PERSON")
        self.assertEqual(res2.entity_type, "POLICE_STATION")
        self.assertNotEqual(
            (res1.case_id, res1.entity_type, res1.normalized_value),
            (res2.case_id, res2.entity_type, res2.normalized_value),
        )

    def test_case_isolation(self) -> None:
        # Same normalized name in different cases must NEVER merge
        cand_case1 = {
            "temp_id": "c1",
            "case_id": 1,
            "fir_id": 10,
            "dataset_image_id": 0,
            "source_evidence_id": 100,
            "extraction_entity_type": "PERSON",
            "raw_value": "John Doe",
            "normalized_value": "John Doe",
        }
        cand_case2 = {
            "temp_id": "c2",
            "case_id": 2,
            "fir_id": 20,
            "dataset_image_id": 1,
            "source_evidence_id": 200,
            "extraction_entity_type": "PERSON",
            "raw_value": "John Doe",
            "normalized_value": "John Doe",
        }
        res1 = self.resolver.resolve_candidate(cand_case1)
        res2 = self.resolver.resolve_candidate(cand_case2)

        self.assertEqual(res1.decision, ResolutionDecision.CREATED_NEW)
        self.assertEqual(res2.decision, ResolutionDecision.CREATED_NEW)

    def test_ambiguous_short_value_kept_separate(self) -> None:
        cand = {
            "temp_id": "c_amb",
            "case_id": 1,
            "fir_id": 10,
            "dataset_image_id": 0,
            "source_evidence_id": 100,
            "extraction_entity_type": "PERSON",
            "raw_value": "A",
            "normalized_value": "A",
        }
        res = self.resolver.resolve_candidate(cand)
        self.assertEqual(res.decision, ResolutionDecision.KEPT_SEPARATE_AMBIGUOUS)

    def test_pilot_scope_guard_rejection(self) -> None:
        db = SessionLocal()
        try:
            with self.assertRaises(PilotScopeError):
                resolve_and_persist_pilot(db=db, requested_image_ids={10})
        finally:
            db.close()


class EntityResolutionPilotIntegrationTests(unittest.TestCase):
    """Database integration tests verifying the 18 requirements against Oracle XE."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.db = SessionLocal()
        cls.handoff, cls.ext_report = extract_pilot_entities(db=cls.db)
        # Execute first run of resolution and persistence
        cls.report1 = resolve_and_persist_pilot(db=cls.db, handoff=cls.handoff)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db.close()

    # Requirement 1: 13 candidates are loaded
    def test_01_thirteen_candidates_loaded(self) -> None:
        self.assertEqual(len(self.handoff["entities"]), 13)
        self.assertEqual(self.report1.total_candidates_processed, 13)

    # Requirement 2: Candidate -> canonical Entity mapping is deterministic
    def test_02_mapping_is_deterministic(self) -> None:
        # 1. Integration mapping: All Airport candidates resolve to the exact same canonical entity ID
        by_id = {r.temp_id: r for r in self.report1.resolutions}
        self.assertEqual(by_id["cand_pilot_003"].canonical_entity_id, by_id["cand_pilot_004"].canonical_entity_id)
        self.assertEqual(by_id["cand_pilot_003"].canonical_entity_id, by_id["cand_pilot_009"].canonical_entity_id)
        self.assertEqual(by_id["cand_pilot_003"].canonical_entity_id, by_id["cand_pilot_010"].canonical_entity_id)
        # All Rubina candidates resolve to the exact same canonical entity ID
        self.assertEqual(by_id["cand_pilot_011"].canonical_entity_id, by_id["cand_pilot_012"].canonical_entity_id)

        # 2. Fresh resolution sequence: First occurrence is CREATED_NEW, second is MATCHED_EXISTING
        fresh_resolver = ConservativeEntityResolver()
        fresh_decisions = {}
        for c in self.handoff["entities"]:
            fresh_decisions[c["temp_id"]] = fresh_resolver.resolve_candidate(c).decision
        self.assertEqual(fresh_decisions["cand_pilot_003"], ResolutionDecision.CREATED_NEW)
        self.assertEqual(fresh_decisions["cand_pilot_004"], ResolutionDecision.MATCHED_EXISTING_SAME_FIR)
        self.assertEqual(fresh_decisions["cand_pilot_011"], ResolutionDecision.CREATED_NEW)
        self.assertEqual(fresh_decisions["cand_pilot_012"], ResolutionDecision.MATCHED_EXISTING_SAME_FIR)

    # Requirement 3: PERSON candidates resolve only to PERSON
    def test_03_person_resolves_only_to_person(self) -> None:
        person_res = [r for r in self.report1.resolutions if r.entity_type == "PERSON"]
        self.assertEqual(len(person_res), 5)
        for r in person_res:
            ent = self.db.get(Entity, r.canonical_entity_id)
            self.assertIsNotNone(ent)
            self.assertEqual(ent.entity_type, EntityType.PERSON)

    # Requirement 4: POLICE_STATION candidates resolve only to POLICE_STATION
    def test_04_police_station_resolves_only_to_police_station(self) -> None:
        ps_res = [r for r in self.report1.resolutions if r.entity_type == "POLICE_STATION"]
        self.assertEqual(len(ps_res), 4)
        for r in ps_res:
            ent = self.db.get(Entity, r.canonical_entity_id)
            self.assertIsNotNone(ent)
            self.assertEqual(ent.entity_type, EntityType.POLICE_STATION)

    # Requirement 5: STATUTE candidates resolve only to STATUTE
    def test_05_statute_resolves_only_to_statute(self) -> None:
        stat_res = [r for r in self.report1.resolutions if r.entity_type == "STATUTE"]
        self.assertEqual(len(stat_res), 4)
        for r in stat_res:
            ent = self.db.get(Entity, r.canonical_entity_id)
            self.assertIsNotNone(ent)
            self.assertEqual(ent.entity_type, EntityType.STATUTE)

    # Requirement 6: Duplicate mentions are preserved
    def test_06_duplicate_mentions_preserved(self) -> None:
        # Rubina Laskar appears twice in image 3; Airport appears twice in image 1 and twice in image 3
        rubina_res = [r for r in self.report1.resolutions if r.normalized_value == "Rubina Laskar"]
        self.assertEqual(len(rubina_res), 2)
        # Both share the same canonical entity ID
        self.assertEqual(rubina_res[0].canonical_entity_id, rubina_res[1].canonical_entity_id)
        # Both must have distinct provenance records
        prov_rows = self.db.scalars(
            select(EntityMentionProvenance).where(EntityMentionProvenance.entity_id == rubina_res[0].canonical_entity_id)
        ).all()
        self.assertEqual(len(prov_rows), 2)
        self.assertNotEqual(prov_rows[0].source_index, prov_rows[1].source_index)

    # Requirement 7: Every retained candidate has provenance
    def test_07_every_retained_candidate_has_provenance(self) -> None:
        self.assertEqual(self.report1.provenance_rows_total, 13)
        pilot_ev_ids = {c["source_evidence_id"] for c in self.handoff["entities"]}
        pilot_prov_count = self.db.scalar(
            select(func.count(EntityMentionProvenance.id)).where(EntityMentionProvenance.evidence_id.in_(pilot_ev_ids))
        )
        self.assertEqual(pilot_prov_count, 13)

    # Requirement 8: Provenance points to the correct Evidence
    def test_08_provenance_points_to_correct_evidence(self) -> None:
        for r in self.report1.resolutions:
            prov = self.db.scalar(
                select(EntityMentionProvenance).where(
                    EntityMentionProvenance.entity_id == r.canonical_entity_id,
                    EntityMentionProvenance.evidence_id == r.source_evidence_id,
                )
            )
            self.assertIsNotNone(prov)
            self.assertEqual(prov.evidence_id, r.source_evidence_id)

    # Requirement 9: Case ownership mismatch is rejected
    def test_09_case_ownership_mismatch_rejected(self) -> None:
        bad_handoff = {
            "entities": [
                {
                    "temp_id": "bad_cand",
                    "case_id": 999999,  # Mismatched case_id
                    "fir_id": self.handoff["entities"][0]["fir_id"],
                    "dataset_image_id": 0,
                    "source_evidence_id": self.handoff["entities"][0]["source_evidence_id"],
                    "extraction_entity_type": "PERSON",
                    "raw_value": "Fake Person",
                    "normalized_value": "Fake Person",
                    "provenance": self.handoff["entities"][0]["provenance"],
                }
            ],
            "relationships": [],
            "metadata": self.handoff["metadata"],
        }
        with self.assertRaises(CaseOwnershipMismatchError):
            resolve_and_persist_pilot(db=self.db, handoff=bad_handoff)

    # Requirement 10: No EntityIdentifier is created unless a real identifier exists
    def test_10_zero_entity_identifiers_created(self) -> None:
        self.assertEqual(self.report1.identifiers_created, 0)
        ident_count = self.db.scalar(select(func.count(EntityIdentifier.id)))
        self.assertEqual(ident_count, 0)

    # Requirement 11: No Relationships are created
    def test_11_zero_relationships_created(self) -> None:
        self.assertEqual(self.report1.relationships_count, 0)

    # Requirement 12: No Analysis is created
    def test_12_zero_analysis_created(self) -> None:
        self.assertEqual(self.report1.analyses_count, 0)

    # Requirement 13: No Alerts are created
    def test_13_zero_alerts_created(self) -> None:
        self.assertEqual(self.report1.alerts_count, 0)

    # Requirement 14 & 15: Rerunning the pilot does not duplicate entities or provenance
    def test_14_and_15_idempotency_no_duplicate_entities_or_provenance(self) -> None:
        report2 = resolve_and_persist_pilot(db=self.db, handoff=self.handoff)
        self.assertEqual(report2.canonical_entities_created, 0)
        self.assertEqual(report2.canonical_entities_reused, self.report1.canonical_entities_total)
        self.assertEqual(report2.provenance_rows_created, 0)
        self.assertEqual(report2.provenance_rows_reused, 13)
        self.assertTrue(report2.is_idempotent_rerun)

        # Confirm exact counts for the pilot remain identical
        pilot_ev_ids = {c["source_evidence_id"] for c in self.handoff["entities"]}
        prov_count = self.db.scalar(
            select(func.count(EntityMentionProvenance.id)).where(EntityMentionProvenance.evidence_id.in_(pilot_ev_ids))
        )
        self.assertEqual(prov_count, 13)
        pilot_entity_ids = {r.canonical_entity_id for r in self.report1.resolutions}
        self.assertEqual(len(pilot_entity_ids), self.report1.canonical_entities_total)

    # Requirement 16: Raw dataset remains unchanged
    def test_16_raw_dataset_hashes_unchanged(self) -> None:
        from app.dataset_ingestion.config import DEFAULT_ARCHIVE_PATH, DEFAULT_DATASET_ROOT

        json_path = DEFAULT_DATASET_ROOT / "FIR_details.json"
        self.assertTrue(json_path.exists(), f"Could not find FIR_details.json at {json_path}")
        h_json = hashlib.sha256(json_path.read_bytes()).hexdigest()
        self.assertEqual(h_json, "693a1e11bd116e2458898e43c48785853b6d6e99439f315b761063c0bb2a357a")

        self.assertTrue(DEFAULT_ARCHIVE_PATH.exists(), f"Could not find zip at {DEFAULT_ARCHIVE_PATH}")
        h_zip = hashlib.sha256(DEFAULT_ARCHIVE_PATH.read_bytes()).hexdigest()
        self.assertEqual(h_zip, "be2026f8355a9cb051b42cc975b635fe56a2f261ba5b60aa4ad7b1de5cf5561b")

    # Requirement 17: Oracle compatibility passes
    def test_17_oracle_compatibility(self) -> None:
        fir_count = self.db.scalar(select(func.count(FIR.id)))
        ev_count = self.db.scalar(select(func.count(Evidence.id)))
        self.assertEqual(fir_count, 544)
        self.assertEqual(ev_count, 544)

    # Requirement 18: Transaction rollback works if persistence fails
    def test_18_transaction_rollback_on_failure(self) -> None:
        initial_ent_count = self.db.scalar(select(func.count(Entity.id)))
        initial_prov_count = self.db.scalar(select(func.count(EntityMentionProvenance.id)))

        # Construct a handoff where the second candidate triggers an error (e.g. non-existent evidence)
        failing_handoff = {
            "entities": [
                {
                    "temp_id": "good_cand",
                    "case_id": self.handoff["entities"][0]["case_id"],
                    "fir_id": self.handoff["entities"][0]["fir_id"],
                    "dataset_image_id": 0,
                    "source_evidence_id": self.handoff["entities"][0]["source_evidence_id"],
                    "extraction_entity_type": "PERSON",
                    "raw_value": "Rollback Test Candidate",
                    "normalized_value": "Rollback Test Candidate",
                    "provenance": self.handoff["entities"][0]["provenance"],
                },
                {
                    "temp_id": "failing_cand",
                    "case_id": self.handoff["entities"][0]["case_id"],
                    "fir_id": self.handoff["entities"][0]["fir_id"],
                    "dataset_image_id": 0,
                    "source_evidence_id": 9999999,  # non-existent evidence
                    "extraction_entity_type": "PERSON",
                    "raw_value": "Failing Candidate",
                    "normalized_value": "Failing Candidate",
                    "provenance": self.handoff["entities"][0]["provenance"],
                },
            ],
            "relationships": [],
            "metadata": self.handoff["metadata"],
        }

        with self.assertRaises(CaseOwnershipMismatchError):
            resolve_and_persist_pilot(db=self.db, handoff=failing_handoff)

        # Assert no partial entities or provenances were saved
        final_ent_count = self.db.scalar(select(func.count(Entity.id)))
        final_prov_count = self.db.scalar(select(func.count(EntityMentionProvenance.id)))
        self.assertEqual(final_ent_count, initial_ent_count)
        self.assertEqual(final_prov_count, initial_prov_count)


if __name__ == "__main__":
    unittest.main()
