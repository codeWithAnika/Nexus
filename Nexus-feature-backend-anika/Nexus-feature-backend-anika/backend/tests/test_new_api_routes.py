import unittest
from fastapi.testclient import TestClient

from app.main import app


class NewAPIRoutesIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_01_health_endpoint(self) -> None:
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"status": "healthy"})

    def test_02_relationships_list(self) -> None:
        r = self.client.get("/api/relationships?case_id=21&limit=10")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("items", data)
        self.assertIn("total", data)
        self.assertGreater(data["total"], 0)
        self.assertLessEqual(len(data["items"]), 10)
        first = data["items"][0]
        self.assertIn("source_entity_id", first)
        self.assertIn("target_entity_id", first)
        self.assertIn("relationship_type", first)

    def test_03_alerts_list_and_status_update(self) -> None:
        r = self.client.get("/api/alerts?case_id=21")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("items", data)
        self.assertGreater(data["total"], 0)
        first_alert = data["items"][0]
        alert_id = first_alert["id"]

        # Update status to ACKNOWLEDGED
        update_r = self.client.put(f"/api/alerts/{alert_id}/status", json={"status": "ACKNOWLEDGED"})
        self.assertEqual(update_r.status_code, 200)
        self.assertEqual(update_r.json()["status"], "ACKNOWLEDGED")

    def test_04_network_graph_visualization(self) -> None:
        r = self.client.get("/api/intelligence/graph/21?limit_nodes=50")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["case_id"], 21)
        self.assertEqual(len(data["nodes"]), 50)
        self.assertIn("nodes", data)
        self.assertIn("edges", data)

    def test_05_reports_generate_and_list(self) -> None:
        # Generate report
        gen_r = self.client.post("/api/reports/generate/21")
        self.assertEqual(gen_r.status_code, 201)
        report_data = gen_r.json()
        self.assertEqual(report_data["case_id"], 21)
        self.assertIn("NCRB Criminal Network Intelligence Report", report_data["title"])
        self.assertIsNotNone(report_data["content"])

        # List reports
        list_r = self.client.get("/api/reports?case_id=21")
        self.assertEqual(list_r.status_code, 200)
        self.assertGreater(list_r.json()["total"], 0)

    def test_06_entity_ai_explanation(self) -> None:
        # Get first entity
        ent_r = self.client.get("/api/entities?case_id=21&limit=1")
        self.assertEqual(ent_r.status_code, 200)
        first_ent = ent_r.json()["items"][0]
        ent_id = first_ent["id"]

        # Request explainable breakdown
        exp_r = self.client.post(f"/api/intelligence/explain/{ent_id}")
        self.assertEqual(exp_r.status_code, 200)
        data = exp_r.json()
        self.assertEqual(data["entity_id"], ent_id)
        self.assertIn("explanation", data)
        self.assertIn("key_factors", data)
        self.assertGreaterEqual(len(data["key_factors"]), 1)
        self.assertIn("confidence", data)

    def test_07_aayush_processing_adapter(self) -> None:
        # Check standard handoff contract
        handoff_r = self.client.get("/api/processing/aayush-handoff")
        self.assertEqual(handoff_r.status_code, 200)
        data = handoff_r.json()
        self.assertIn("entities", data)
        self.assertIn("relationships", data)
        self.assertIn("metadata", data)
        self.assertEqual(data["metadata"]["source"], "aayush_processing")

        # Check cross validation
        cv_r = self.client.get("/api/processing/cross-validate")
        self.assertEqual(cv_r.status_code, 200)
        cv_data = cv_r.json()
        self.assertIn("alignment_verdict", cv_data)
        self.assertIn("match_rate_percent", cv_data)
        self.assertIn("overlap_by_type", cv_data)


if __name__ == "__main__":
    unittest.main()
