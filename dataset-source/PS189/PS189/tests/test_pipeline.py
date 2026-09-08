"""
Automated unit and integration test suite for the Data & Evidence Processing Pipeline.
Uses Python's standard unittest framework.
"""
import json
from pathlib import Path
import sys
import unittest
from pydantic import ValidationError
from rapidfuzz import fuzz

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from processing.schema import Entity, StructuredFIR
from processing.dataset_loader import load_and_group_fir_details
from processing.text_cleaner import clean_ocr_text, clean_grouped_records
from processing.entity_extractor import derive_fir_id, extract_entities_for_records, EntityIDGenerator
from processing.deduplicator import deduplicate_entities


class TestProcessingPipeline(unittest.TestCase):

    def test_schema_strictness(self):
        """Verify that Entity and StructuredFIR strictly validate attributes and reject unknown types."""
        valid_entity = Entity(id="P0001", type="PERSON", value="John Doe")
        self.assertEqual(valid_entity.id, "P0001")
        self.assertEqual(valid_entity.type, "PERSON")
        self.assertEqual(valid_entity.value, "John Doe")

        # Reject invalid entity type
        with self.assertRaises(ValidationError):
            Entity(id="X0001", type="ORGANIZATION", value="Invalid Corp")  # type: ignore

        # Reject extra fields
        with self.assertRaises(ValidationError):
            Entity(id="P0001", type="PERSON", value="John Doe", confidence=0.99)  # type: ignore

        valid_fir = StructuredFIR(
            fir_id="FIR_TEST",
            source_image="test__1.jpg",
            entities=[valid_entity],
            relationships=[],
        )
        self.assertEqual(valid_fir.fir_id, "FIR_TEST")
        self.assertEqual(len(valid_fir.entities), 1)
        self.assertEqual(valid_fir.relationships, [])

    def test_derive_fir_id(self):
        """Verify clean derivation of FIR IDs from image names."""
        self.assertEqual(derive_fir_id("Electronics Complex PS5__1.jpg"), "Electronics Complex PS5")
        self.assertEqual(derive_fir_id("Women PSWOMEN-0032-2017-1422__1.jpg"), "Women PSWOMEN-0032-2017-1422")
        self.assertEqual(derive_fir_id("Baguiati PS514-18__1.jpg"), "Baguiati PS514-18")
        self.assertEqual(derive_fir_id("Cyber-Crime PS47-20__2.png"), "Cyber-Crime PS47-20")

    def test_text_cleaner_score_filtering(self):
        """Verify records with score < 0.60 are dropped and text is cleaned."""
        grouped = {
            "img1.jpg": [
                {"score": 0.59, "text": "Low score text", "category_id": 3},
                {"score": 0.60, "text": " Valid   Text  \" ", "category_id": 3},
                {"score": 0.95, "text": "High score text", "category_id": 0},
            ]
        }
        cleaned = clean_grouped_records(grouped, min_score=0.60)
        self.assertEqual(len(cleaned["img1.jpg"]), 2)
        self.assertEqual(cleaned["img1.jpg"][0]["text"], "Valid Text")
        self.assertEqual(cleaned["img1.jpg"][1]["text"], "High score text")

    def test_deduplication_rapidfuzz(self):
        """Verify rapidfuzz deduplicates entities >90% similar within the same type."""
        entities = [
            Entity(id="P0001", type="PERSON", value="Kamaljit Kaur"),
            Entity(id="P0002", type="PERSON", value="Kamaljit Kaur."),  # >90% similar, duplicate
            Entity(id="P0003", type="PERSON", value="Harpreet Singh"),    # distinct person
            Entity(id="D0001", type="DATE", value="2017"),
            Entity(id="D0002", type="DATE", value="2017"),              # duplicate date
        ]
        deduped = deduplicate_entities(entities, similarity_threshold=90.0)
        self.assertEqual(len(deduped), 3)
        self.assertEqual([e.id for e in deduped], ["P0001", "P0003", "D0001"])

    def test_output_json_integrity(self):
        """Verify the generated structured_evidence_output.json against all requirements."""
        output_path = Path("structured_evidence_output.json")
        self.assertTrue(output_path.exists(), "structured_evidence_output.json must exist")

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 544, f"Expected 544 FIR records, got {len(data)}")

        all_entity_ids = set()
        total_entities = 0
        allowed_types = {"LOCATION", "DATE", "CRIME TYPE", "PERSON"}

        for item in data:
            # Validate through strict Pydantic model
            fir = StructuredFIR.model_validate(item)

            # Check clean fir_id
            self.assertFalse(fir.fir_id.endswith(".jpg"))
            self.assertFalse(fir.fir_id.endswith(".png"))
            self.assertNotIn("__", fir.fir_id)

            # Check relationships list is empty
            self.assertEqual(fir.relationships, [])

            # Check entity constraints
            fir_entities_by_type = {}
            for ent in fir.entities:
                self.assertIn(ent.type, allowed_types, f"Invented category found: {ent.type}")
                self.assertNotIn(ent.id, all_entity_ids, f"Duplicate entity id: {ent.id}")
                all_entity_ids.add(ent.id)
                total_entities += 1

                fir_entities_by_type.setdefault(ent.type, []).append(ent.value)

            # Check rapidfuzz deduplication within this FIR
            for etype, vals in fir_entities_by_type.items():
                for i in range(len(vals)):
                    for j in range(i + 1, len(vals)):
                        ratio = fuzz.ratio(vals[i].lower(), vals[j].lower())
                        self.assertLessEqual(
                            ratio,
                            90.0,
                            f"Found duplicate in FIR {fir.fir_id} ({etype}): '{vals[i]}' and '{vals[j]}' (ratio {ratio})"
                        )

        self.assertEqual(total_entities, 1856, f"Expected 1856 total entities, got {total_entities}")


if __name__ == "__main__":
    unittest.main()
