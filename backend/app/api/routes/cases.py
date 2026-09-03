from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.case import CaseCreate, CaseResponse, CaseUpdate
from app.services.case_service import (
    CaseDatabaseError,
    CaseHasRelatedRecordsError,
    CaseNotFoundError,
    CreatorNotFoundError,
    DuplicateCaseNumberError,
    create_case,
    delete_case,
    get_case,
    get_cases,
    update_case,
)

router = APIRouter(prefix="/api/cases", tags=["cases"])
DbSession = Annotated[Session, Depends(get_db)]


def _database_error() -> HTTPException:
    return HTTPException(status_code=500, detail="Database operation failed")


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case_endpoint(payload: CaseCreate, db: DbSession) -> CaseResponse:
    try:
        return create_case(db, payload.model_dump())
    except CreatorNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Creator user not found") from exc
    except DuplicateCaseNumberError as exc:
        raise HTTPException(status_code=409, detail="Case number already exists") from exc
    except CaseDatabaseError as exc:
        raise _database_error() from exc


@router.get("", response_model=list[CaseResponse])
def list_cases(
    db: DbSession,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[CaseResponse]:
    try:
        return list(get_cases(db, skip=skip, limit=limit))
    except CaseDatabaseError as exc:
        raise _database_error() from exc


@router.get("/{case_id}", response_model=CaseResponse)
def read_case(case_id: int, db: DbSession) -> CaseResponse:
    try:
        return get_case(db, case_id)
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc
    except CaseDatabaseError as exc:
        raise _database_error() from exc


@router.put("/{case_id}", response_model=CaseResponse)
def update_case_endpoint(case_id: int, payload: CaseUpdate, db: DbSession) -> CaseResponse:
    try:
        return update_case(db, case_id, payload.model_dump(exclude_unset=True))
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc
    except DuplicateCaseNumberError as exc:
        raise HTTPException(status_code=409, detail="Case number already exists") from exc
    except CaseDatabaseError as exc:
        raise _database_error() from exc


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_case(case_id: int, db: DbSession) -> Response:
    try:
        delete_case(db, case_id)
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc
    except CaseHasRelatedRecordsError as exc:
        raise HTTPException(status_code=409, detail="Case has related records and cannot be deleted safely") from exc
    except CaseDatabaseError as exc:
        raise _database_error() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)