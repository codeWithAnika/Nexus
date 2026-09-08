import json
import unittest

from app.database.connection import SessionLocal
from app.entity_extraction.config import DEFAULT_CONFIG, ExtractionConfig, PILOT_IMAGE_IDS
from app.entity_extraction.extractor import PilotScopeError, extract_pilot_entities
from app.entity_extraction.models import ExtractionEntityType, TextSpan
from app.entity_extraction.normalizer import (
    normalize_person_name,
    normalize_police_station,
    normalize_statute,
)
from app.entity_extraction.rules import extract_from_category_3


class EntityExtractionPilotUnitTests(unittest.TestCase):
    def test_text_span_validation(self) -> None:
        text = "Si Jayanta Nath Saha, Baguiati P.S"
        valid_span = TextSpan(start_char=3, end_char=20, matched_text="Jayanta Nath Saha")
        self.assertTrue(valid_span.validate(text))

        invalid_span = TextSpan(start_char=0, end_char=5, matched_text="Wrong")
        self.assertFalse(invalid_span.validate(text))

        oob_span = TextSpan(start_char=-1, end_char=10, matched_text="test")
        self.assertFalse(oob_span.validate(text))

    def test_person_normalization(self) -> None:
        self.assertEqual(normalize_person_name("Si Sahabuddin Mondal"), "Sahabuddin Mondal")
        self.assertEqual(normalize_person_name("Sri Indranil Roy"), "Indranil Roy")
        self.assertEqual(normalize_person_name("Monodip Das Gupta"), "Monodip Das Gupta")
        self.assertEqual(normalize_person_name("P.K. Sen"), "P.K. Sen")
        self.assertEqual(normalize_person_name("DR. ANAND SHARMA"), "Anand Sharma")

    def test_police_station_normalization(self) -> None:
        self.assertEqual(normalize_police_station("Airport "), "Airport Police Station")
        self.assertEqual(normalize_police_station("Baguiati P.S"), "Baguiati Police Station")
        self.assertEqual(normalize_police_station("Electronics Complex "), "Electronics Complex Police Station")

    def test_statute_normalization(self) -> None:
        self.assertEqual(
            normalize_statute("420/406/120B Ipc"),
            "IPC_420 | IPC_406 | IPC_120B",
        )
        self.assertEqual(
            normalize_statute("399/402 Ipc And 25(I)(A)/27 Arms Act"),
            "IPC_399 | IPC_402 | ARMS ACT_25(I)(A) | ARMS ACT_27",
        )

    def test_category_3_multi_span_splitting(self) -> None:
        text = "Si Jayanta Nath Saha, Baguiati P.S"
        candidates = extract_from_category_3(text)
        self.assertEqual(len(candidates), 2)
        # Person
        self.assertEqual(candidates[0].entity_type, ExtractionEntityType.PERSON)
        self.assertEqual(candidates[0].raw_value, "Si Jayanta Nath Saha")
        self.assertEqual(candidates[0].normalized_value, "Jayanta Nath Saha")
        self.assertTrue(candidates[0].span.validate(text))
        # Police station
        self.assertEqual(candidates[1].entity_type, ExtractionEntityType.POLICE_STATION)
        self.assertEqual(candidates[1].raw_value, "Baguiati P.S")
        self.assertEqual(candidates[1].normalized_value, "Baguiati Police Station")
        self.assertTrue(candidates[1].span.validate(text))

    def test_is_plausible_person_name(self) -> None:
        from app.entity_extraction.rules import is_plausible_person_name

        # Legitimate pilot and standard names
        self.assertTrue(is_plausible_person_name("Si Sahabuddin Mondal"))
        self.assertTrue(is_plausible_person_name("Sri Indranil Roy"))
        self.assertTrue(is_plausible_person_name("Monodip Das Gupta"))
        self.assertTrue(is_plausible_person_name("Rubina Laskar"))
        self.assertTrue(is_plausible_person_name("Si Jayanta Nath Saha"))
        self.assertTrue(is_plausible_person_name("P.K. Sen"))
        self.assertTrue(is_plausible_person_name("Md. Goni"))
        self.assertTrue(is_plausible_person_name("Dr. Anand Sharma"))

        # Obvious false positives that must be rejected
        self.assertFalse(is_plausible_person_name(""))
        self.assertFalse(is_plausible_person_name("   "))
        self.assertFalse(is_plausible_person_name("2018"))
        self.assertFalse(is_plausible_person_name("420/406/120B Ipc"))
        self.assertFalse(is_plausible_person_name("Airport P.S"))
        self.assertFalse(is_plausible_person_name("Baguiati Police Station"))
        self.assertFalse(is_plausible_person_name("25(I)(A)/27 Arms Act"))
        self.assertFalse(is_plausible_person_name("---"))
        self.assertFalse(is_plausible_person_name("12345"))
        self.assertFalse(is_plausible_person_name("!@#$"))
        self.assertFalse(is_plausible_person_name("A"))
        self.assertFalse(is_plausible_person_name("P."))
        self.assertFalse(is_plausible_person_name("Dr."))

    def test_category_3_rejection_of_false_positives(self) -> None:
        # Administrative strings or noise passed to category 3 should yield empty candidates
        self.assertEqual(extract_from_category_3(""), [])
        self.assertEqual(extract_from_category_3("2018"), [])
        self.assertEqual(extract_from_category_3("420/406/120B Ipc"), [])
        self.assertEqual(extract_from_category_3("25(I)(A)/27 Arms Act"), [])
        self.assertEqual(extract_from_category_3("Airport P.S"), [])
        self.assertEqual(extract_from_category_3("12345"), [])
        self.assertEqual(extract_from_category_3("---"), [])

    def test_safety_guard_rejects_non_pilot_images(self) -> None:
        db = SessionLocal()
        try:
            with self.assertRaises(PilotScopeError):
                extract_pilot_entities(db=db, requested_image_ids={5})
            with self.assertRaises(PilotScopeError):
                extract_pilot_entities(db=db, requested_image_ids={0, 100})
        finally:
            db.close()


class EntityExtractionPilotRealDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db = SessionLocal()
        cls.handoff, cls.report = extract_pilot_entities(db=cls.db)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db.close()

    def test_exactly_five_images_processed(self) -> None:
        self.assertEqual(self.report.total_images_processed, 5)
        self.assertEqual(set(self.report.pilot_image_ids), {0, 1, 2, 3, 4})

    def test_ocr_record_counts(self) -> None:
        # Sum of OCR records across images 0-4: Image0=2, Image1=5, Image2=2, Image3=5, Image4=1 -> Total=15
        self.assertEqual(self.report.ocr_records_processed, 15)

    def test_category_1_exclusion(self) -> None:
        # Category 1 (Year) must not produce standalone entity candidates
        for entity in self.handoff["entities"]:
            self.assertNotEqual(entity["provenance"]["category_id"], 1)

    def test_relationships_must_be_empty(self) -> None:
        self.assertEqual(self.handoff["relationships"], [])
        self.assertEqual(self.report.relationships_count, 0)

    def test_no_entity_resolution(self) -> None:
        self.assertFalse(self.report.entity_resolution_performed)

    def test_no_database_migrations_or_schema_changes(self) -> None:
        self.assertFalse(self.report.database_migrations_created)

    def test_provenance_and_character_spans(self) -> None:
        for entity in self.handoff["entities"]:
            prov = entity["provenance"]
            orig_text = prov["original_text"]
            span = prov["span"]
            self.assertEqual(orig_text[span["start_char"]:span["end_char"]], span["matched_text"])
            self.assertEqual(entity["raw_value"], span["matched_text"])
            self.assertIn(prov["category_id"], {0, 2, 3})
            self.assertGreater(prov["ocr_score"], 0.0)
            self.assertEqual(len(prov["bbox"]), 4)

    def test_confidence_separation_and_formula(self) -> None:
        for entity in self.handoff["entities"]:
            c_ocr = entity["ocr_confidence"]
            c_ext = entity["extraction_confidence"]
            c_final = entity["entity_confidence"]
            expected_final = round((0.30 * c_ocr) + (0.70 * c_ext), 4)
            self.assertEqual(c_final, expected_final)
            if c_ocr < 0.60:
                self.assertTrue(entity["low_ocr_confidence"])
            else:
                self.assertFalse(entity["low_ocr_confidence"])

    def test_duplicate_mentions_preserved(self) -> None:
        # Rubina Laskar appears twice in Image 3 and Airport appears twice in Image 1 & 3
        self.assertGreaterEqual(self.report.duplicate_mentions_preserved, 1)
        image3_persons = [e for e in self.handoff["entities"] if e["dataset_image_id"] == 3 and e["extraction_entity_type"] == "PERSON"]
        self.assertEqual(len(image3_persons), 2)
        # Both must have different temp_id and different source_index
        self.assertNotEqual(image3_persons[0]["temp_id"], image3_persons[1]["temp_id"])
        self.assertNotEqual(image3_persons[0]["provenance"]["source_index"], image3_persons[1]["provenance"]["source_index"])

    def test_unsupported_db_taxonomy_flagged(self) -> None:
        # POLICE_STATION and STATUTE have been extended into EntityType and are now natively supported
        self.assertEqual(self.report.unsupported_db_taxonomy_count, 0)
        found_types = {entity["extraction_entity_type"] for entity in self.handoff["entities"]}
        self.assertIn("POLICE_STATION", found_types)
        self.assertIn("STATUTE", found_types)
        self.assertIn("PERSON", found_types)


if __name__ == "__main__":
    unittest.main()
