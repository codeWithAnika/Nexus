from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.evidence import Evidence
from app.models.fir import FIR
from app.models.relationship import Relationship


# ---------------------------------------------------------------------------
# Custom exceptions — mirrors the pattern in case_service / entity_service
# ---------------------------------------------------------------------------

class FIRServiceError(Exception):
    pass


class FIRNotFoundError(FIRServiceError):
    pass


class FIRCaseNotFoundError(FIRServiceError):
    pass


class FIRNumberDuplicateError(FIRServiceError):
    pass


class FIRDatasetImageIdDuplicateError(FIRServiceError):
    pass


class FIRHasDependentsError(FIRServiceError):
    pass


class FIRDatabaseError(FIRServiceError):
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _case_exists(db: Session, case_id: int) -> bool:
    return db.scalar(select(Case.id).where(Case.id == case_id)) is not None


def _dataset_image_id_taken(db: Session, dataset_image_id: int, exclude_fir_id: int | None = None) -> bool:
    stmt = select(FIR.id).where(FIR.dataset_image_id == dataset_image_id)
    if exclude_fir_id is not None:
        stmt = stmt.where(FIR.id != exclude_fir_id)
    return db.scalar(stmt) is not None


def _fir_number_taken(db: Session, fir_number: str, exclude_fir_id: int | None = None) -> bool:
    stmt = select(FIR.id).where(FIR.fir_number == fir_number)
    if exclude_fir_id is not None:
        stmt = stmt.where(FIR.id != exclude_fir_id)
    return db.scalar(stmt) is not None


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

def create_fir(db: Session, fir_data: dict, *, commit: bool = True) -> FIR:
    try:
        if not _case_exists(db, fir_data["case_id"]):
            raise FIRCaseNotFoundError

        if _fir_number_taken(db, fir_data["fir_number"]):
            raise FIRNumberDuplicateError

        dataset_image_id = fir_data.get("dataset_image_id")
        if dataset_image_id is not None and _dataset_image_id_taken(db, dataset_image_id):
            raise FIRDatasetImageIdDuplicateError

        fir = FIR(**fir_data)
        db.add(fir)
        if commit:
            db.commit()
            db.refresh(fir)
        else:
            db.flush()
        return fir

    except (FIRCaseNotFoundError, FIRNumberDuplicateError, FIRDatasetImageIdDuplicateError):
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        # Catch any DB-level uniqueness violation not caught above
        raise FIRDatabaseError from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise FIRDatabaseError from exc


def get_fir(db: Session, fir_id: int) -> FIR:
    try:
        fir = db.get(FIR, fir_id)
    except SQLAlchemyError as exc:
        raise FIRDatabaseError from exc
    if fir is None:
        raise FIRNotFoundError
    return fir


def list_firs(
    db: Session,
    *,
    case_id: int | None,
    dataset_image_id: int | None,
    fir_number: str | None,
    skip: int,
    limit: int,
) -> tuple[Sequence[FIR], int]:
    try:
        filters = []
        if case_id is not None:
            filters.append(FIR.case_id == case_id)
        if dataset_image_id is not None:
            filters.append(FIR.dataset_image_id == dataset_image_id)
        if fir_number is not None:
            filters.append(FIR.fir_number == fir_number)

        items = db.scalars(
            select(FIR)
            .where(*filters)
            .order_by(FIR.created_at.desc(), FIR.id.desc())
            .offset(skip)
            .limit(limit)
        ).all()
        total = db.scalar(select(func.count(FIR.id)).where(*filters))
        return items, int(total or 0)

    except SQLAlchemyError as exc:
        raise FIRDatabaseError from exc


def update_fir(db: Session, fir_id: int, updates: dict) -> FIR:
    fir = get_fir(db, fir_id)
    try:
        new_fir_number = updates.get("fir_number")
        if new_fir_number is not None and _fir_number_taken(db, new_fir_number, exclude_fir_id=fir_id):
            raise FIRNumberDuplicateError

        new_dataset_image_id = updates.get("dataset_image_id")
        if new_dataset_image_id is not None and _dataset_image_id_taken(db, new_dataset_image_id, exclude_fir_id=fir_id):
            raise FIRDatasetImageIdDuplicateError

        for field, value in updates.items():
            setattr(fir, field, value)

        db.commit()
        db.refresh(fir)
        return fir

    except (FIRNumberDuplicateError, FIRDatasetImageIdDuplicateError):
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise FIRDatabaseError from exc


def delete_fir(db: Session, fir_id: int) -> None:
    fir = get_fir(db, fir_id)
    try:
        # Oracle does not support SELECT EXISTS (SELECT * ...) AS anon FROM DUAL.
        # Use COUNT-based checks instead, which are valid on all supported dialects.
        evidence_count = db.scalar(
            select(func.count(Evidence.id)).where(Evidence.fir_id == fir_id)
        )
        relationship_count = db.scalar(
            select(func.count(Relationship.id)).where(Relationship.source_fir_id == fir_id)
        )
        if (evidence_count or 0) > 0 or (relationship_count or 0) > 0:
            raise FIRHasDependentsError

        db.delete(fir)
        db.commit()

    except FIRHasDependentsError:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise FIRHasDependentsError from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise FIRDatabaseError from exc
