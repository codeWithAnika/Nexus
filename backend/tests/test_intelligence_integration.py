from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import SessionLocal
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.models.analysis import Analysis, RiskLevel
from app.models.case import Case
from app.models.entity import Entity, EntityMentionProvenance, EntityType
from app.models.evidence import Evidence
from app.models.fir import FIR
from app.models.relationship import Relationship, RelationshipType
from app.services.intelligence_integration_service import (
    CaseNotFoundError,
    IdMapper,
    IntelligenceIntegrationError,
    IntelligenceIntegrationService,
    InvalidEntityReferenceError,
    map_alert_severity_to_oracle,
    map_entity_type_to_aayushman,
    map_relationship_type_to_oracle,
    map_risk_tier_to_oracle,
    resolve_external_fir_reference,
)


class IntelligenceIntegrationUnitTests(unittest.TestCase):
    """Unit tests verifying mapping functions, ID translation, and safety boundaries."""

    def test_id_mapper_bidirectional(self) -> None:
        mapper = IdMapper()
        mapper.register(45, "ENT-45")
        mapper.register(46, "ENT-46")

        self.assertEqual(mapper.get_db_id("ENT-45"), 45)
        self.assertEqual(mapper.get_db_id("ENT-46"), 46)
        self.assertEqual(mapper.get_aayushman_id(45), "ENT-45")
        self.assertEqual(mapper.get_aayushman_id(46), "ENT-46")
        self.assertIsNone(mapper.get_db_id("ENT-UNKNOWN"))
        self.assertIsNone(mapper.get_aayushman_id(999))

    def test_map_entity_type_conservative(self) -> None:
        """Verify conservative entity taxonomy mappings."""
        # PERSON -> Person
        p_res = map_entity_type_to_aayushman(EntityType.PERSON)
        self.assertEqual(p_res.value, "Person")

        # LOCATION -> Location
        l_res = map_entity_type_to_aayushman(EntityType.LOCATION)
        self.assertEqual(l_res.value, "Location")

        # POLICE_STATION -> Location (topological node)
        ps_res = map_entity_type_to_aayushman(EntityType.POLICE_STATION)
        self.assertEqual(ps_res.value, "Location")

        # STATUTE -> CaseRef (conservative; does NOT become a Person or Location)
        st_res = map_entity_type_to_aayushman(EntityType.STATUTE)
        self.assertEqual(st_res.value, "CaseRef")
        self.assertNotEqual(st_res.value, "Person")
        self.assertNotEqual(st_res.value, "Location")

    def test_map_relationship_type_oracle(self) -> None:
        from fir_intelligence.phase2_graph.models import RelationType

        self.assertEqual(map_relationship_type_to_oracle(RelationType.OWNS), RelationshipType.OWNS)
        self.assertEqual(map_relationship_type_to_oracle(RelationType.USES), RelationshipType.COMMUNICATED_WITH)
        self.assertEqual(map_relationship_type_to_oracle(RelationType.VISITED), RelationshipType.LOCATED_AT)
        self.assertEqual(map_relationship_type_to_oracle(RelationType.TRANSACTION), RelationshipType.TRANSFERRED_TO)
        self.assertEqual(map_relationship_type_to_oracle(RelationType.CONNECTED_TO), RelationshipType.ASSOCIATED_WITH)
        self.assertEqual(map_relationship_type_to_oracle(RelationType.ASSOCIATED_WITH), RelationshipType.ASSOCIATED_WITH)

    def test_map_risk_tier_to_oracle(self) -> None:
        self.assertEqual(map_risk_tier_to_oracle("LOW"), RiskLevel.LOW)
        self.assertEqual(map_risk_tier_to_oracle("MEDIUM"), RiskLevel.MEDIUM)
        self.assertEqual(map_risk_tier_to_oracle("HIGH"), RiskLevel.HIGH)
        self.assertEqual(map_risk_tier_to_oracle("CRITICAL"), RiskLevel.CRITICAL)
        self.assertEqual(map_risk_tier_to_oracle("unknown"), RiskLevel.LOW)

    def test_map_alert_severity_to_oracle(self) -> None:
        self.assertEqual(map_alert_severity_to_oracle("LOW"), AlertSeverity.LOW)
        self.assertEqual(map_alert_severity_to_oracle("MEDIUM"), AlertSeverity.MEDIUM)
        self.assertEqual(map_alert_severity_to_oracle("HIGH"), AlertSeverity.HIGH)
        self.assertEqual(map_alert_severity_to_oracle("CRITICAL"), AlertSeverity.CRITICAL)


class IntelligenceIntegrationDBTests(unittest.TestCase):
    """Integration tests running against the live Oracle XE database."""

    def setUp(self) -> None:
        self.db = SessionLocal()

    def tearDown(self) -> None:
        self.db.close()

    def test_fir_reference_resolver(self) -> None:
        """Verify external FIR references map to correct Oracle FIR ID."""
        fir_0 = self.db.scalar(select(FIR).where(FIR.dataset_image_id == 0))
        self.assertIsNotNone(fir_0)

        # 1. By integer ID string
        self.assertEqual(resolve_external_fir_reference(str(fir_0.id), self.db), fir_0.id)

        # 2. By FIR-<id>
        self.assertEqual(resolve_external_fir_reference(f"FIR-{fir_0.id}", self.db), fir_0.id)

        # 3. By fir_number
        self.assertEqual(resolve_external_fir_reference(fir_0.fir_number, self.db), fir_0.id)

        # 4. By ICDAR-<image_id>
        self.assertEqual(resolve_external_fir_reference("ICDAR-0", self.db), fir_0.id)

        # 5. Non-existent returns None
        self.assertIsNone(resolve_external_fir_reference("FIR-999999", self.db))
        self.assertIsNone(resolve_external_fir_reference("", self.db))

    def test_pilot_intelligence_run_and_idempotency(self) -> None:
        """
        Runs intelligence over pilot images {0, 1, 2, 3, 4} in Case 21.
        Verifies:
        - 9 pilot entities evaluated
        - Transaction succeeds
        - Repeated run does not create duplicate analyses or alerts
        - No orphan relationships
        """
        service = IntelligenceIntegrationService(self.db)
        case_id = 21

        # Run 1
        res1 = service.run_intelligence_pipeline(case_id=case_id, requested_image_ids={0, 1, 2, 3, 4})
        self.assertEqual(res1["case_id"], case_id)
        self.assertEqual(res1["entities_evaluated"], 9)
        self.assertEqual(res1["status"], "completed")

        # Run 2 (Idempotency test)
        res2 = service.run_intelligence_pipeline(case_id=case_id, requested_image_ids={0, 1, 2, 3, 4})
        self.assertEqual(res2["case_id"], case_id)
        self.assertEqual(res2["entities_evaluated"], 9)
        # Idempotency: second run should not create duplicate entities/analyses/alerts
        self.assertEqual(res2["relationships_created"], 0)
        self.assertEqual(res2["analyses_created"], 0)
        self.assertEqual(res2["alerts_created"], 0)

        # Verify Analysis records exist in DB for evaluated entities
        analyses = self.db.scalars(
            select(Analysis).where(
                Analysis.case_id == case_id,
                Analysis.analysis_type == "GRAPH_INTELLIGENCE_RISK",
            )
        ).all()
        self.assertGreaterEqual(len(analyses), 9)

        # Verify no orphan relationships exist
        all_rels = self.db.scalars(select(Relationship)).all()
        for r in all_rels:
            self.assertIsNotNone(self.db.scalar(select(Entity.id).where(Entity.id == r.source_entity_id)))
            self.assertIsNotNone(self.db.scalar(select(Entity.id).where(Entity.id == r.target_entity_id)))

        # Test completed successfully

    def test_nonexistent_case_raises_404(self) -> None:
        service = IntelligenceIntegrationService(self.db)
        with self.assertRaises(CaseNotFoundError):
            service.run_intelligence_pipeline(case_id=999999)

    def test_intelligence_transaction_rollback(self) -> None:
        """Verify that failure during persistence cleanly rolls back the transaction."""
        service = IntelligenceIntegrationService(self.db)
        case_id = 21

        rel_before = self.db.query(Relationship).count()
        ana_before = self.db.query(Analysis).count()
        alt_before = self.db.query(Alert).count()

        # Patch Alert addition or commit to raise an intentional error
        with patch.object(self.db, "commit", side_effect=SQLAlchemyError("Simulated write failure")):
            with self.assertRaises(IntelligenceIntegrationError):
                service.run_intelligence_pipeline(case_id=case_id, requested_image_ids={0, 1})

        # Ensure database has zero half-created rows (state restored to baseline)
        self.assertEqual(self.db.query(Relationship).count(), rel_before)
        self.assertEqual(self.db.query(Analysis).count(), ana_before)
        self.assertEqual(self.db.query(Alert).count(), alt_before)


class FullDatasetIntegrityTests(unittest.TestCase):
    """Verifies dataset discovery, hash integrity, and full-scope metrics."""

    def test_dataset_hash_and_discovery(self) -> None:
        import hashlib, json
        from app.dataset_ingestion.config import DEFAULT_DATASET_ROOT

        json_path = DEFAULT_DATASET_ROOT / "FIR_details.json"
        self.assertTrue(json_path.exists())

        with open(json_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(h, "693a1e11bd116e2458898e43c48785853b6d6e99439f315b761063c0bb2a357a")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data), 2447)
        distinct_ids = {r["image_id"] for r in data}
        self.assertEqual(len(distinct_ids), 544)


if __name__ == "__main__":
    unittest.main()
