from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.user import User


class CaseServiceError(Exception):
    pass


class CreatorNotFoundError(CaseServiceError):
    pass


class CaseNotFoundError(CaseServiceError):
    pass


class DuplicateCaseNumberError(CaseServiceError):
    pass


class CaseHasRelatedRecordsError(CaseServiceError):
    pass


class CaseDatabaseError(CaseServiceError):
    pass


def create_case(db: Session, case_data: dict) -> Case:
    try:
        if db.scalar(select(User.id).where(User.id == case_data["created_by"])) is None:
            raise CreatorNotFoundError
        if db.scalar(select(Case.id).where(Case.case_number == case_data["case_number"])) is not None:
            raise DuplicateCaseNumberError

        case = Case(**case_data)
        db.add(case)
        db.commit()
        db.refresh(case)
        return case
    except (CreatorNotFoundError, DuplicateCaseNumberError):
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateCaseNumberError from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise CaseDatabaseError from exc


def get_cases(db: Session, skip: int = 0, limit: int = 100) -> Sequence[Case]:
    try:
        return db.scalars(select(Case).order_by(Case.created_at.desc(), Case.id.desc()).offset(skip).limit(limit)).all()
    except SQLAlchemyError as exc:
        raise CaseDatabaseError from exc


def get_case(db: Session, case_id: int) -> Case:
    try:
        case = db.get(Case, case_id)
    except SQLAlchemyError as exc:
        raise CaseDatabaseError from exc
    if case is None:
        raise CaseNotFoundError
    return case


def update_case(db: Session, case_id: int, updates: dict) -> Case:
    case = get_case(db, case_id)
    try:
        if "case_number" in updates and db.scalar(select(Case.id).where(Case.case_number == updates["case_number"], Case.id != case_id)) is not None:
            raise DuplicateCaseNumberError
        for field, value in updates.items():
            setattr(case, field, value)
        db.commit()
        db.refresh(case)
        return case
    except DuplicateCaseNumberError:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateCaseNumberError from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise CaseDatabaseError from exc


def delete_case(db: Session, case_id: int) -> None:
    case = get_case(db, case_id)
    if any(getattr(case, relation) for relation in ("firs", "evidence", "entities", "analyses", "alerts", "investigations", "reports")):
        raise CaseHasRelatedRecordsError
    try:
        db.delete(case)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CaseHasRelatedRecordsError from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise CaseDatabaseError from exc