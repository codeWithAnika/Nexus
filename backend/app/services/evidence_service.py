import json
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.case import Case
from app.models.evidence import Evidence, EvidenceType


class EvidenceServiceError(Exception):
    pass


class EvidenceNotFoundError(EvidenceServiceError):
    pass


class EvidenceCaseNotFoundError(EvidenceServiceError):
    pass


class EvidenceHasDependentsError(EvidenceServiceError):
    pass


class EvidenceDatabaseError(EvidenceServiceError):
    pass


def metadata_with_description(description: str | None, original_filename: str) -> str:
    metadata = {"original_filename": original_filename}
    if description is not None:
        metadata["description"] = description
    return json.dumps(metadata, ensure_ascii=True)


def create_evidence(db: Session, *, case_id: int, evidence_type: EvidenceType, file_name: str, file_path: str, mime_type: str | None, file_hash: str, metadata_text: str) -> Evidence:
    try:
        if db.scalar(select(Case.id).where(Case.id == case_id)) is None:
            raise EvidenceCaseNotFoundError
        evidence = Evidence(case_id=case_id, evidence_type=evidence_type, file_name=file_name, file_path=file_path, mime_type=mime_type, file_hash=file_hash, metadata_text=metadata_text)
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
        return evidence
    except EvidenceCaseNotFoundError:
        db.rollback()
        raise
    except (IntegrityError, SQLAlchemyError) as exc:
        db.rollback()
        raise EvidenceDatabaseError from exc


def get_evidence(db: Session, evidence_id: int) -> Evidence:
    try:
        evidence = db.get(Evidence, evidence_id)
    except SQLAlchemyError as exc:
        raise EvidenceDatabaseError from exc
    if evidence is None:
        raise EvidenceNotFoundError
    return evidence


def list_evidence(db: Session, *, case_id: int | None, skip: int, limit: int) -> tuple[Sequence[Evidence], int]:
    try:
        filters = [Evidence.case_id == case_id] if case_id is not None else []
        items = db.scalars(select(Evidence).where(*filters).order_by(Evidence.created_at.desc(), Evidence.id.desc()).offset(skip).limit(limit)).all()
        total = db.scalar(select(func.count(Evidence.id)).where(*filters))
        return items, int(total or 0)
    except SQLAlchemyError as exc:
        raise EvidenceDatabaseError from exc


def update_evidence(db: Session, evidence_id: int, updates: dict) -> Evidence:
    evidence = get_evidence(db, evidence_id)
    try:
        if "description" in updates:
            metadata = json.loads(evidence.metadata_text or "{}")
            metadata["description"] = updates.pop("description")
            updates["metadata_text"] = json.dumps(metadata, ensure_ascii=True)
        for field, value in updates.items():
            setattr(evidence, field, value)
        db.commit()
        db.refresh(evidence)
        return evidence
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        db.rollback()
        raise EvidenceDatabaseError from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise EvidenceDatabaseError from exc


def delete_evidence(db: Session, evidence_id: int) -> str | None:
    evidence = get_evidence(db, evidence_id)
    try:
        # Oracle does not support SELECT EXISTS (SELECT * ...) AS anon FROM DUAL.
        # Use COUNT to check for dependent Analysis rows — valid on all supported dialects.
        analysis_count = db.scalar(
            select(func.count(Analysis.id)).where(Analysis.source_evidence_id == evidence_id)
        )
        if evidence.identifiers or evidence.relationships or (analysis_count or 0) > 0:
            raise EvidenceHasDependentsError
        file_path = evidence.file_path
        db.delete(evidence)
        db.commit()
        return file_path
    except EvidenceHasDependentsError:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise EvidenceHasDependentsError from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise EvidenceDatabaseError from exc