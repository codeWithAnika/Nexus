import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.dialects.oracle import dialect as oracle_dialect
from sqlalchemy.orm import Session

from app.database.base import Base
from app.dataset_ingestion.identity import technical_fir_number
from app.dataset_ingestion.importer import run_import
from app.dataset_ingestion.models import ImportStatus, OCRInput
from app.dataset_ingestion.ocr import reconstruct_ocr
from app.dataset_ingestion.preflight import PreflightError, run_preflight
from app.dataset_ingestion import storage
from scripts.ingest_fir_dataset import main as ingest_cli_main, validate_handoff_output_path
from app.models.case import Case, CasePriority, CaseStatus
from app.models.evidence import Evidence, EvidenceType
from app.models.fir import FIR
from app.models.user import User, UserRole


class DatasetFixtures:
    def __init__(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "dataset"
        self.image_root = self.root / "FIR_images_v1"
        self.image_root.mkdir(parents=True)
        self.image_path = self.image_root / "Station PS1-2021__1.jpg"
        self.image_path.write_bytes(b"image-one")
        records = [
            {"image_id": 7, "bbox": [100, 100, 140, 120], "score": 0.9, "category_id": 1, "image_name": self.image_path.name, "text": "2021"},
            {"image_id": 7, "bbox": [10, 10, 60, 30], "score": 0.8, "category_id": 0, "image_name": self.image_path.name, "text": " Station  "},
            {"image_id": 7, "bbox": [10, 10, 60, 30], "score": 0.7, "category_id": 0, "image_name": self.image_path.name, "text": " Station  "},
        ]
        (self.root / "FIR_details.json").write_text(json.dumps(records), encoding="utf-8")
        self.archive = Path(self.temp_dir.name) / "archive.zip"
        self.archive.write_bytes(b"archive")

    def close(self) -> None:
        self.temp_dir.cleanup()


class DatasetIngestionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures = DatasetFixtures()

    def tearDown(self) -> None:
        self.fixtures.close()

    def test_preflight_and_dry_run_do_not_write(self) -> None:
        report = run_preflight(self.fixtures.root)
        self.assertEqual(report.annotated_image_count, 1)
        self.assertEqual(report.ocr_record_count, 3)
        self.assertEqual(report.duplicate_ocr_records, 1)
        before = sorted(path.relative_to(self.fixtures.root).as_posix() for path in self.fixtures.root.rglob("*"))
        result = run_import(
            dataset_root=self.fixtures.root,
            archive_path=self.fixtures.archive,
            case_id="TEST",
        )
        after = sorted(path.relative_to(self.fixtures.root).as_posix() for path in self.fixtures.root.rglob("*"))
        self.assertEqual(result.imported, 0)
        self.assertEqual(result.results[0].status, ImportStatus.PROPOSED)
        self.assertEqual(before, after)
        self.assertEqual(result.handoff[0].fir_id, None)

    def test_preflight_rejects_malformed_records(self) -> None:
        payload_path = self.fixtures.root / "FIR_details.json"
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        payload[0]["bbox"] = [1, 2, 3]
        payload_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(PreflightError):
            run_preflight(self.fixtures.root)

    def test_preflight_rejects_conflicting_image_mapping(self) -> None:
        payload_path = self.fixtures.root / "FIR_details.json"
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        payload.append({**payload[0], "image_name": "other.jpg"})
        (self.fixtures.image_root / "other.jpg").write_bytes(b"other")
        payload_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(PreflightError):
            run_preflight(self.fixtures.root)

    def test_ocr_order_and_duplicate_preservation(self) -> None:
        records = [
            OCRInput(2, 1, "x.jpg", (100, 40, 150, 60), 0.9, 1, "right"),
            OCRInput(1, 1, "x.jpg", (10, 40, 50, 60), 0.9, 1, " left  "),
            OCRInput(0, 1, "x.jpg", (10, 10, 40, 25), 0.9, 0, "top"),
        ]
        reconstruction = reconstruct_ocr(records)
        self.assertEqual(reconstruction.extracted_text, "top left right")
        self.assertEqual(len(reconstruction.records), 3)
        self.assertEqual([record.reconstructed_order for record in reconstruction.records], [0, 1, 2])
        self.assertEqual(reconstruction.records[1].original_text, " left  ")

    def test_identity_is_deterministic(self) -> None:
        self.assertEqual(technical_fir_number(452), "ICDAR-452")

    def test_ingestion_queries_compile_for_oracle(self) -> None:
        fir_query = select(FIR.id).where(FIR.dataset_image_id == 7)
        evidence_query = select(Evidence.id).where(Evidence.fir_id == 11)
        self.assertIn("SELECT", str(fir_query.compile(dialect=oracle_dialect())))
        self.assertIn("SELECT", str(evidence_query.compile(dialect=oracle_dialect())))

    def _session(self) -> Session:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.addCleanup(engine.dispose)
        return Session(engine)

    def _case(self, session: Session, number: str) -> Case:
        user = User(username=f"{number}-user", email=f"{number}@example.com", password_hash="x", role=UserRole.ADMIN, is_active=True)
        session.add(user)
        session.flush()
        case = Case(case_number=number, title="Test", status=CaseStatus.OPEN, priority=CasePriority.MEDIUM, created_by=user.id)
        session.add(case)
        session.flush()
        session.commit()
        return case

    def _storage_root(self) -> tempfile.TemporaryDirectory[str]:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        return directory

    def test_existing_import_is_detected(self) -> None:
        session = self._session()
        archive_hash = hashlib.sha256(self.fixtures.archive.read_bytes()).hexdigest()
        image_hash = hashlib.sha256(self.fixtures.image_path.read_bytes()).hexdigest()
        user = User(username="tester", email="tester@example.com", password_hash="x", role=UserRole.ADMIN, is_active=True)
        session.add(user)
        session.flush()
        case = Case(case_number="CASE-1", title="Test", status=CaseStatus.OPEN, priority=CasePriority.MEDIUM, created_by=user.id)
        session.add(case)
        session.flush()
        fir = FIR(case_id=case.id, fir_number="ICDAR-7", dataset_image_id=7, source_file=self.fixtures.image_path.name)
        session.add(fir)
        session.flush()
        evidence = Evidence(
            case_id=case.id,
            fir_id=fir.id,
            evidence_type=EvidenceType.IMAGE,
            file_name=self.fixtures.image_path.name,
            file_hash=image_hash,
            metadata_text=json.dumps({"dataset_name": "FIR_Dataset_ICDAR2023", "archive_sha256": archive_hash, "dataset_image_id": 7}),
        )
        session.add(evidence)
        session.commit()
        report = run_import(dataset_root=self.fixtures.root, archive_path=self.fixtures.archive, case_id=case.id, db=session, inspect_db=True)
        self.assertEqual(report.already_imported, 1)
        session.close()

    def test_missing_evidence_is_resumed(self) -> None:
        session = self._session()
        user = User(username="tester2", email="tester2@example.com", password_hash="x", role=UserRole.ADMIN, is_active=True)
        session.add(user)
        session.flush()
        case = Case(case_number="CASE-2", title="Test", status=CaseStatus.OPEN, priority=CasePriority.MEDIUM, created_by=user.id)
        session.add(case)
        session.flush()
        session.add(FIR(case_id=case.id, fir_number="ICDAR-7", dataset_image_id=7, source_file=self.fixtures.image_path.name))
        session.commit()
        report = run_import(dataset_root=self.fixtures.root, archive_path=self.fixtures.archive, case_id=case.id, db=session, inspect_db=True)
        self.assertEqual(report.resumed, 1)
        session.close()

    def test_non_string_text_is_rejected(self) -> None:
        payload_path = self.fixtures.root / "FIR_details.json"
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        payload[0]["text"] = 2021
        payload_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(PreflightError, "expected a string"):
            run_preflight(self.fixtures.root)

    def test_handoff_output_inside_dataset_is_rejected(self) -> None:
        inside = self.fixtures.root / "handoff.jsonl"
        with self.assertRaisesRegex(ValueError, "outside dataset_root"):
            validate_handoff_output_path(inside, self.fixtures.root)

    def test_cli_inspect_db_passes_integer_case_id(self) -> None:
        session = object()
        with patch.object(sys, "argv", [
            "ingest_fir_dataset.py",
            "--case-id", "21",
            "--dataset-root", str(self.fixtures.root),
            "--archive", str(self.fixtures.archive),
            "--dry-run",
            "--inspect-db",
        ]), patch("app.database.connection.SessionLocal") as session_factory, patch(
            "scripts.ingest_fir_dataset.run_import",
            return_value=SimpleNamespace(failed=0, conflicts=0, handoff=[]),
        ) as run_import, patch("scripts.ingest_fir_dataset.report_json", return_value="{}"):
            session_factory.return_value.__enter__.return_value = session
            self.assertEqual(ingest_cli_main(), 0)
        self.assertIs(run_import.call_args.kwargs["case_id"], 21)

    def test_existing_storage_is_preserved_after_transaction_failure(self) -> None:
        session = self._session()
        case = self._case(session, "CASE-STORAGE")
        root = self._storage_root()
        image_hash = hashlib.sha256(self.fixtures.image_path.read_bytes()).hexdigest()
        destination = Path(root.name) / f"fir_dataset_7_{image_hash[:16]}.jpg"
        destination.write_bytes(b"existing")
        with patch.object(storage, "STORAGE_ROOT", Path(root.name)), patch("app.dataset_ingestion.importer.create_evidence", side_effect=RuntimeError("forced failure")):
            report = run_import(dataset_root=self.fixtures.root, archive_path=self.fixtures.archive, case_id=case.id, db=session, execute=True)
        self.assertEqual(report.failed, 1)
        self.assertEqual(destination.read_bytes(), b"existing")
        session.close()

    def test_partial_copy_failure_leaves_no_final_or_temporary_file(self) -> None:
        root = self._storage_root()
        source = Path(root.name) / "source.jpg"
        source.write_bytes(b"source")
        image_hash = hashlib.sha256(source.read_bytes()).hexdigest()

        def partial_copy(_source: Path, destination: Path) -> None:
            destination.write_bytes(b"partial")
            raise OSError("forced copy failure")

        with patch.object(storage, "STORAGE_ROOT", Path(root.name)), patch.object(storage.shutil, "copyfile", side_effect=partial_copy):
            with self.assertRaises(OSError):
                storage.copy_image(source, 8, image_hash)
        self.assertFalse((Path(root.name) / f"fir_dataset_8_{image_hash[:16]}.jpg").exists())
        self.assertEqual(list(Path(root.name).glob("*.tmp")), [])

    def test_resume_case_mismatch_is_conflict_without_changes(self) -> None:
        session = self._session()
        case_a = self._case(session, "CASE-A")
        case_b = self._case(session, "CASE-B")
        fir = FIR(case_id=case_a.id, fir_number="ICDAR-7", dataset_image_id=7, source_file=self.fixtures.image_path.name)
        session.add(fir)
        session.flush()
        evidence = Evidence(case_id=case_a.id, fir_id=fir.id, evidence_type=EvidenceType.IMAGE, file_name="old.jpg", file_hash="old", metadata_text="{}")
        session.add(evidence)
        session.commit()
        with patch("app.dataset_ingestion.importer.copy_image") as copy:
            report = run_import(dataset_root=self.fixtures.root, archive_path=self.fixtures.archive, case_id=case_b.id, db=session, execute=True)
        self.assertEqual(report.conflicts, 1)
        self.assertIn("another Case", report.results[0].reason or "")
        copy.assert_not_called()
        self.assertEqual(session.get(FIR, fir.id).case_id, case_a.id)
        self.assertEqual(session.query(Evidence).count(), 1)
        session.close()

    def test_hash_conflict_does_not_overwrite(self) -> None:
        session = self._session()
        case = self._case(session, "CASE-HASH")
        fir = FIR(case_id=case.id, fir_number="ICDAR-7", dataset_image_id=7, source_file=self.fixtures.image_path.name)
        session.add(fir)
        session.flush()
        evidence = Evidence(case_id=case.id, fir_id=fir.id, evidence_type=EvidenceType.IMAGE, file_name="old.jpg", file_hash="different", metadata_text="{}")
        session.add(evidence)
        session.commit()
        with patch("app.dataset_ingestion.importer.copy_image") as copy:
            report = run_import(dataset_root=self.fixtures.root, archive_path=self.fixtures.archive, case_id=case.id, db=session, execute=True)
        self.assertEqual(report.conflicts, 1)
        copy.assert_not_called()
        self.assertEqual(session.get(Evidence, evidence.id).file_hash, "different")
        session.close()

    def test_evidence_persistence(self) -> None:
        session = self._session()
        case = self._case(session, "CASE-EVIDENCE")
        root = self._storage_root()
        with patch.object(storage, "STORAGE_ROOT", Path(root.name)):
            report = run_import(dataset_root=self.fixtures.root, archive_path=self.fixtures.archive, case_id=case.id, db=session, execute=True)
        self.assertEqual(report.imported, 1)
        evidence = session.query(Evidence).one()
        self.assertEqual(evidence.fir_id, session.query(FIR).one().id)
        self.assertEqual(evidence.case_id, case.id)
        self.assertEqual(evidence.file_name, self.fixtures.image_path.name)
        self.assertEqual(evidence.file_hash, hashlib.sha256(self.fixtures.image_path.read_bytes()).hexdigest())
        self.assertEqual(evidence.mime_type, "image/jpeg")
        self.assertEqual(evidence.source, "FIR_Dataset_ICDAR2023")
        self.assertIn("2021", evidence.extracted_text or "")
        self.assertIn("archive_sha256", evidence.metadata_text or "")
        self.assertEqual(evidence.evidence_type, EvidenceType.IMAGE)
        session.close()

    def test_transaction_rollback_removes_fir_and_new_storage(self) -> None:
        session = self._session()
        case = self._case(session, "CASE-ROLLBACK")
        root = self._storage_root()
        with patch.object(storage, "STORAGE_ROOT", Path(root.name)), patch("app.dataset_ingestion.importer.create_evidence", side_effect=RuntimeError("forced failure")):
            report = run_import(dataset_root=self.fixtures.root, archive_path=self.fixtures.archive, case_id=case.id, db=session, execute=True)
        self.assertEqual(report.failed, 1)
        self.assertEqual(session.query(FIR).count(), 0)
        self.assertEqual(list(Path(root.name).glob("*")), [])
        session.close()


if __name__ == "__main__":
    unittest.main()
