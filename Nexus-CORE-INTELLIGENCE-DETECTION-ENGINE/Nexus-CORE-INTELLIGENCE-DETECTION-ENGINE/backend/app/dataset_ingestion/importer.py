from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dataset_ingestion.config import DATASET_NAME
from app.dataset_ingestion.identity import sha256_file, technical_fir_number
from app.dataset_ingestion.models import HandoffRecord, ImageResult, ImportReport, ImportStatus
from app.dataset_ingestion.ocr import reconstruct_ocr
from app.dataset_ingestion.preflight import run_preflight
from app.dataset_ingestion.provenance import build_provenance, provenance_text
from app.dataset_ingestion.storage import copy_image, inspect_image, remove_stored_image
from app.models.case import Case
from app.models.evidence import Evidence, EvidenceType
from app.models.fir import FIR
from app.services.evidence_service import create_evidence
from app.services.fir_service import create_fir


def _existing_identity(
    db: Session,
    image_id: int,
    image_sha256: str,
    archive_sha256: str,
    case_id: int | str,
) -> tuple[ImportStatus | None, str | None]:
    fir = db.scalar(select(FIR).where(FIR.dataset_image_id == image_id))
    if fir is None:
        return None, None
    if fir.case_id != case_id:
        return ImportStatus.CONFLICT, "dataset_image_id already belongs to another Case"
    evidence_rows = list(db.scalars(select(Evidence).where(Evidence.fir_id == fir.id)).all())
    if not evidence_rows:
        return ImportStatus.RESUMED, "FIR exists without source Evidence"
    matching = []
    for evidence in evidence_rows:
        try:
            metadata = json.loads(evidence.metadata_text or "{}")
        except json.JSONDecodeError:
            continue
        matching.append(
            evidence.file_hash == image_sha256
            and metadata.get("dataset_name") == DATASET_NAME
            and metadata.get("archive_sha256") == archive_sha256
            and metadata.get("dataset_image_id") == image_id
        )
    if len(evidence_rows) == 1 and matching == [True]:
        return ImportStatus.ALREADY_IMPORTED, "matching FIR and source Evidence already exist"
    return ImportStatus.CONFLICT, "existing image identity has conflicting Evidence"


def run_import(
    *,
    dataset_root: Path,
    archive_path: Path,
    case_id: int | str,
    db: Session | None = None,
    execute: bool = False,
    inspect_db: bool = False,
) -> ImportReport:
    preflight = run_preflight(dataset_root)
    archive_sha256 = sha256_file(archive_path)
    if execute and db is None:
        raise ValueError("An existing database session is required for execution")
    if inspect_db and db is None:
        raise ValueError("An existing database session is required for database inspection")
    if execute and (not isinstance(case_id, int) or db.scalar(select(Case.id).where(Case.id == case_id)) is None):
        raise ValueError(f"Case does not exist: {case_id}")
    report = ImportReport(
        total_annotated_images=preflight.annotated_image_count,
        unreferenced_images=len(preflight.unreferenced_images),
    )
    for image in preflight.images:
        image_sha256 = inspect_image(image.path)
        reconstruction = reconstruct_ocr(image.records)
        provenance = build_provenance(
            archive_sha256=archive_sha256,
            dataset_image_id=image.image_id,
            image_name=image.image_name,
            image_sha256=image_sha256,
            reconstruction=reconstruction,
        )
        if not execute:
            if inspect_db:
                status, reason = _existing_identity(db, image.image_id, image_sha256, archive_sha256, case_id)
            else:
                status, reason = None, None
            if status is None:
                status = ImportStatus.PROPOSED
                reason = "dry-run; no database or storage writes performed"
            report.add(ImageResult(image.image_id, image.image_name, status, reason))
            if status in {ImportStatus.PROPOSED, ImportStatus.ALREADY_IMPORTED, ImportStatus.RESUMED}:
                report.handoff.append(HandoffRecord(None, None, image.image_id, image.image_name, reconstruction.extracted_text, provenance))
            continue

        stored_path: str | None = None
        status: ImportStatus | None = None
        reason: str | None = None
        try:
            db.rollback()
            with db.begin():
                status, reason = _existing_identity(db, image.image_id, image_sha256, archive_sha256, case_id)
                if status not in {ImportStatus.ALREADY_IMPORTED, ImportStatus.CONFLICT}:
                    stored = copy_image(image.path, image.image_id, image_sha256)
                    stored_path = stored.file_path if stored.created else None
                    fir = db.scalar(select(FIR).where(FIR.dataset_image_id == image.image_id))
                    if fir is None:
                        fir = create_fir(
                            db,
                            {
                                "case_id": case_id,
                                "fir_number": technical_fir_number(image.image_id),
                                "dataset_image_id": image.image_id,
                                "source_file": image.image_name,
                            },
                            commit=False,
                        )
                    evidence = create_evidence(
                        db,
                        case_id=case_id,
                        fir_id=fir.id,
                        evidence_type=EvidenceType.IMAGE,
                        file_name=image.image_name,
                        file_path=stored.file_path,
                        mime_type="image/jpeg",
                        file_hash=image_sha256,
                        source=DATASET_NAME,
                        extracted_text=reconstruction.extracted_text,
                        metadata_text=provenance_text(provenance),
                        commit=False,
                    )
            if status in {ImportStatus.ALREADY_IMPORTED, ImportStatus.CONFLICT}:
                report.add(ImageResult(image.image_id, image.image_name, status, reason))
                if status == ImportStatus.ALREADY_IMPORTED:
                    fir = db.scalar(select(FIR).where(FIR.dataset_image_id == image.image_id))
                    evidence = db.scalar(select(Evidence).where(Evidence.fir_id == fir.id)) if fir else None
                    report.handoff.append(HandoffRecord(fir.id if fir else None, evidence.id if evidence else None, image.image_id, image.image_name, reconstruction.extracted_text, provenance))
                continue
            result_status = ImportStatus.RESUMED if status == ImportStatus.RESUMED else ImportStatus.IMPORTED
            report.add(ImageResult(image.image_id, image.image_name, result_status))
            report.handoff.append(HandoffRecord(fir.id, evidence.id, image.image_id, image.image_name, reconstruction.extracted_text, provenance))
        except Exception as exc:
            if stored_path:
                remove_stored_image(stored_path)
            db.rollback()
            report.add(ImageResult(image.image_id, image.image_name, ImportStatus.FAILED, str(exc)))
    return report
