import unittest
from pathlib import Path
from unittest.mock import patch

from app.services import intelligence_integration_service as integration


class IntelligenceEngineDiscoveryTests(unittest.TestCase):
    def test_discovers_repository_engine(self) -> None:
        expected = Path(__file__).resolve().parents[1].parent / "CORE INTELLIGENCE - DETECTION ENGINE"
        self.assertEqual(integration._discover_fir_intelligence_root(), expected.resolve())

    def test_missing_engine_is_explicit(self) -> None:
        with patch.object(integration, "aay_p1", None), patch.object(integration, "FIR_INTELLIGENCE_IMPORT_ERROR", "engine missing"):
            with self.assertRaises(integration.IntelligenceEngineUnavailableError):
                integration.IntelligenceIntegrationService(None).run_intelligence_pipeline(1)


if __name__ == "__main__":
    unittest.main()