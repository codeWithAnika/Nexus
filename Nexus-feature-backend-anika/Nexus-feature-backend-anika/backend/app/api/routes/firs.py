from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.fir import FIRCreate, FIRListResponse, FIRResponse, FIRUpdate
from app.services.fir_service import (
    FIRCaseNotFoundError,
    FIRDatabaseError,
    FIRDatasetImageIdDuplicateError,
    FIRHasDependentsError,
    FIRNotFoundError,
    FIRNumberDuplicateError,
    create_fir,
    delete_fir,
    get_fir,
    list_firs,
    update_fir,
)

router = APIRouter(prefix="/api/firs", tags=["firs"])
DbSession = Annotated[Session, Depends(get_db)]


def _database_error() -> HTTPException:
    return HTTPException(status_code=500, detail="Database operation failed")


@router.post("", response_model=FIRResponse, status_code=status.HTTP_201_CREATED)
def create_fir_endpoint(payload: FIRCreate, db: DbSession) -> FIRResponse:
    try:
        return create_fir(db, payload.model_dump())
    except FIRCaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc
    except FIRNumberDuplicateError as exc:
        raise HTTPException(status_code=409, detail="FIR number already exists") from exc
    except FIRDatasetImageIdDuplicateError as exc:
        raise HTTPException(status_code=409, detail="dataset_image_id already assigned to another FIR") from exc
    except FIRDatabaseError as exc:
        raise _database_error() from exc


@router.get("", response_model=FIRListResponse)
def list_firs_endpoint(
    db: DbSession,
    case_id: int | None = Query(default=None, gt=0),
    dataset_image_id: int | None = Query(default=None, gt=0),
    fir_number: str | None = Query(default=None, min_length=1, max_length=100),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> FIRListResponse:
    try:
        items, total = list_firs(
            db,
            case_id=case_id,
            dataset_image_id=dataset_image_id,
            fir_number=fir_number,
            skip=skip,
            limit=limit,
        )
        return FIRListResponse(items=list(items), total=total, skip=skip, limit=limit)
    except FIRDatabaseError as exc:
        raise _database_error() from exc


@router.get("/{fir_id}", response_model=FIRResponse)
def read_fir(fir_id: int, db: DbSession) -> FIRResponse:
    try:
        return get_fir(db, fir_id)
    except FIRNotFoundError as exc:
        raise HTTPException(status_code=404, detail="FIR not found") from exc
    except FIRDatabaseError as exc:
        raise _database_error() from exc


@router.put("/{fir_id}", response_model=FIRResponse)
def update_fir_endpoint(fir_id: int, payload: FIRUpdate, db: DbSession) -> FIRResponse:
    try:
        return update_fir(db, fir_id, payload.model_dump(exclude_unset=True))
    except FIRNotFoundError as exc:
        raise HTTPException(status_code=404, detail="FIR not found") from exc
    except FIRNumberDuplicateError as exc:
        raise HTTPException(status_code=409, detail="FIR number already exists") from exc
    except FIRDatasetImageIdDuplicateError as exc:
        raise HTTPException(status_code=409, detail="dataset_image_id already assigned to another FIR") from exc
    except FIRDatabaseError as exc:
        raise _database_error() from exc


@router.delete("/{fir_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_fir(fir_id: int, db: DbSession) -> Response:
    try:
        delete_fir(db, fir_id)
    except FIRNotFoundError as exc:
        raise HTTPException(status_code=404, detail="FIR not found") from exc
    except FIRHasDependentsError as exc:
        raise HTTPException(
            status_code=409,
            detail="FIR has dependent evidence or relationships and cannot be deleted safely",
        ) from exc
    except FIRDatabaseError as exc:
        raise _database_error() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
