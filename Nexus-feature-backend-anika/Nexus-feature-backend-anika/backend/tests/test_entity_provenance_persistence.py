import unittest
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.database.connection import SessionLocal
from app.models.case import Case, CasePriority, CaseStatus
from app.models.entity import Entity, EntityMentionProvenance, EntityType
from app.models.evidence import Evidence, EvidenceType
from app.models.fir import FIR
from app.models.user import User, UserRole
from app.services.entity_service import (
    EntityHasDependentsError,
    EntityProvenanceDuplicateError,
    EntityProvenanceEvidenceNotFoundError,
    create_entity,
    create_mention_provenance,
    delete_entity,
    list_mention_provenances,
)
from app.services.evidence_service import EvidenceHasDependentsError, delete_evidence
from app.services.fir_service import FIRHasDependentsError, delete_fir


class EntityProvenancePersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = SessionLocal()
        # Create test user
        self.user = User(
            username="test_prov_user",
            email="test_prov_user@nexus.gov.in",
            password_hash="test_hash",
            full_name="Test Prov User",
            role=UserRole.INVESTIGATOR,
        )
        self.db.add(self.user)
        self.db.commit()
        self.db.refresh(self.user)

        # Create test case 1
        self.case = Case(
            case_number="CASE-PROV-TEST-001",
            title="Entity Provenance Test Case",
            description="Testing EntityMentionProvenance",
            status=CaseStatus.OPEN,
            priority=CasePriority.MEDIUM,
            created_by=self.user.id,
        )
        self.db.add(self.case)

        # Create test case 2 (for cross-case consistency check)
        self.case_other = Case(
            case_number="CASE-PROV-TEST-002",
            title="Other Case",
            description="Other case for cross-case test",
            status=CaseStatus.OPEN,
            priority=CasePriority.LOW,
            created_by=self.user.id,
        )
        self.db.add(self.case_other)
        self.db.commit()
        self.db.refresh(self.case)
        self.db.refresh(self.case_other)

        # Create FIR in case 1
        self.fir = FIR(
            case_id=self.case.id,
            fir_number="FIR-PROV-TEST-001",
            police_station="Airport PS",
            registration_date=date(2021, 5, 10),
        )
        self.db.add(self.fir)
        self.db.commit()
        self.db.refresh(self.fir)

        # Create Evidence in case 1
        self.evidence = Evidence(
            case_id=self.case.id,
            fir_id=self.fir.id,
            evidence_type=EvidenceType.IMAGE,
            file_name="test_image.jpg",
            metadata_text="{}",
        )
        # Create Evidence in case 2
        self.evidence_other = Evidence(
            case_id=self.case_other.id,
            fir_id=None,
            evidence_type=EvidenceType.INTELLIGENCE_REPORT,
            file_name="other_evidence.pdf",
            metadata_text="{}",
        )
        self.db.add(self.evidence)
        self.db.add(self.evidence_other)
        self.db.commit()
        self.db.refresh(self.evidence)
        self.db.refresh(self.evidence_other)

    def tearDown(self) -> None:
        self.db.rollback()
        # Clean up only test-created rows in reverse dependency order
        try:
            self.db.query(EntityMentionProvenance).filter(
                EntityMentionProvenance.evidence_id.in_([self.evidence.id, self.evidence_other.id])
            ).delete(synchronize_session=False)
            self.db.query(Entity).filter(
                Entity.case_id.in_([self.case.id, self.case_other.id])
            ).delete(synchronize_session=False)
            self.db.query(Evidence).filter(
                Evidence.id.in_([self.evidence.id, self.evidence_other.id])
            ).delete(synchronize_session=False)
            self.db.query(FIR).filter(
                FIR.id == self.fir.id
            ).delete(synchronize_session=False)
            self.db.query(Case).filter(
                Case.id.in_([self.case.id, self.case_other.id])
            ).delete(synchronize_session=False)
            self.db.query(User).filter(
                User.id == self.user.id
            ).delete(synchronize_session=False)
            self.db.commit()
        except Exception:
            self.db.rollback()
        finally:
            self.db.close()

    def test_entity_type_taxonomy_acceptance(self) -> None:
        # POLICE_STATION and STATUTE accepted natively
        ps = create_entity(
            self.db,
            {
                "case_id": self.case.id,
                "entity_type": EntityType.POLICE_STATION,
                "name": "Airport Police Station",
                "normalized_name": "Airport Police Station",
            },
        )
        self.assertEqual(ps.entity_type, EntityType.POLICE_STATION)

        st = create_entity(
            self.db,
            {
                "case_id": self.case.id,
                "entity_type": EntityType.STATUTE,
                "name": "420/406 IPC",
                "normalized_name": "IPC_420 | IPC_406",
            },
        )
        self.assertEqual(st.entity_type, EntityType.STATUTE)

        # IDENTIFIER must not be an EntityType member
        self.assertNotIn("IDENTIFIER", EntityType.__members__)

    def test_create_mention_provenance_and_case_consistency(self) -> None:
        entity = create_entity(
            self.db,
            {
                "case_id": self.case.id,
                "entity_type": EntityType.PERSON,
                "name": "Rubina Laskar",
                "normalized_name": "Rubina Laskar",
            },
        )

        # 1. Attempt creating provenance with evidence from another case -> must fail
        with self.assertRaises(EntityProvenanceEvidenceNotFoundError):
            create_mention_provenance(
                self.db,
                entity.id,
                {
                    "evidence_id": self.evidence_other.id,  # belongs to case_other!
                    "matched_text": "Rubina Laskar",
                    "extraction_confidence": 0.92,
                    "final_confidence": 0.85,
                    "extraction_method": "test_rule_v1",
                    "extractor_version": "2.1.0",
                },
            )

        # 2. Valid creation with matching evidence
        prov1 = create_mention_provenance(
            self.db,
            entity.id,
            {
                "evidence_id": self.evidence.id,
                "matched_text": "Rubina Laskar",
                "start_char": 0,
                "end_char": 13,
                "ocr_confidence": 0.5891,
                "extraction_confidence": 0.92,
                "final_confidence": 0.8207,
                "low_ocr_confidence": True,
                "extraction_method": "category_3_complainant_person_rule_v1",
                "extractor_version": "2.1.0",
                "source_index": 492,
                "reconstructed_order": 3,
                "category_id": 3,
                "bbox_x1": 205.97,
                "bbox_y1": 384.85,
                "bbox_x2": 400.67,
                "bbox_y2": 414.55,
                "original_text": "Rubina Laskar",
            },
        )
        self.assertIsNotNone(prov1.id)
        self.assertEqual(prov1.matched_text, "Rubina Laskar")
        self.assertTrue(prov1.low_ocr_confidence)

        # 3. Same entity with multiple provenance rows (e.g. second mention at source_index 490)
        prov2 = create_mention_provenance(
            self.db,
            entity.id,
            {
                "evidence_id": self.evidence.id,
                "matched_text": "Rubina Laskar",
                "start_char": 0,
                "end_char": 13,
                "ocr_confidence": 0.6870,
                "extraction_confidence": 0.92,
                "final_confidence": 0.8501,
                "low_ocr_confidence": False,
                "extraction_method": "category_3_complainant_person_rule_v1",
                "extractor_version": "2.1.0",
                "source_index": 490,
                "reconstructed_order": 4,
                "category_id": 3,
                "bbox_x1": 217.16,
                "bbox_y1": 387.68,
                "bbox_x2": 534.95,
                "bbox_y2": 416.38,
                "original_text": "Rubina Laskar",
            },
        )
        self.assertIsNotNone(prov2.id)

        mentions = list_mention_provenances(self.db, entity.id)
        self.assertEqual(len(mentions), 2)

    def test_duplicate_mention_uniqueness_enforced(self) -> None:
        entity = create_entity(
            self.db,
            {
                "case_id": self.case.id,
                "entity_type": EntityType.PERSON,
                "name": "Monodip Das Gupta",
                "normalized_name": "Monodip Das Gupta",
            },
        )
        prov_payload = {
            "evidence_id": self.evidence.id,
            "matched_text": "Monodip Das Gupta",
            "start_char": 0,
            "end_char": 17,
            "source_index": 807,
            "extraction_confidence": 0.92,
            "final_confidence": 0.9155,
            "extraction_method": "test_rule_v1",
            "extractor_version": "2.1.0",
        }
        create_mention_provenance(self.db, entity.id, prov_payload)

        # Second insertion with exact same (evidence_id, source_index, start_char, end_char) must be rejected
        with self.assertRaises(EntityProvenanceDuplicateError):
            create_mention_provenance(self.db, entity.id, prov_payload)

    def test_nullable_icdar_fields_for_generic_evidence(self) -> None:
        entity = create_entity(
            self.db,
            {
                "case_id": self.case_other.id,
                "entity_type": EntityType.ORGANIZATION,
                "name": "Shell Company Ltd",
                "normalized_name": "Shell Company Ltd",
            },
        )
        # Non-ICDAR generic evidence: source_index, bboxes, ocr_confidence are all None
        prov = create_mention_provenance(
            self.db,
            entity.id,
            {
                "evidence_id": self.evidence_other.id,
                "matched_text": "Shell Company Ltd",
                "extraction_confidence": 0.95,
                "final_confidence": 0.95,
                "low_ocr_confidence": False,
                "extraction_method": "intelligence_report_ner_v1",
                "extractor_version": "2.1.0",
            },
        )
        self.assertIsNone(prov.source_index)
        self.assertIsNone(prov.category_id)
        self.assertIsNone(prov.bbox_x1)
        self.assertIsNone(prov.ocr_confidence)

    def test_deletion_blocked_by_provenance(self) -> None:
        entity = create_entity(
            self.db,
            {
                "case_id": self.case.id,
                "entity_type": EntityType.PERSON,
                "name": "Sahabuddin Mondal",
                "normalized_name": "Sahabuddin Mondal",
            },
        )
        create_mention_provenance(
            self.db,
            entity.id,
            {
                "evidence_id": self.evidence.id,
                "matched_text": "Sahabuddin Mondal",
                "start_char": 0,
                "end_char": 17,
                "extraction_confidence": 0.92,
                "final_confidence": 0.8508,
                "extraction_method": "test_rule_v1",
                "extractor_version": "2.1.0",
            },
        )

        # 1. Attempt deleting Entity -> blocked by provenance
        with self.assertRaises(EntityHasDependentsError):
            delete_entity(self.db, entity.id)

        # 2. Attempt deleting Evidence -> blocked by provenance
        with self.assertRaises(EvidenceHasDependentsError):
            delete_evidence(self.db, self.evidence.id)

        # 3. Attempt deleting FIR -> blocked by dependent Evidence
        with self.assertRaises(FIRHasDependentsError):
            delete_fir(self.db, self.fir.id)


if __name__ == "__main__":
    unittest.main()
