import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.evidence import EvidenceType
from app.schemas.evidence import EvidenceListResponse, EvidenceResponse, EvidenceUpdate
from app.services.evidence_service import (
    EvidenceCaseNotFoundError,
    EvidenceDatabaseError,
    EvidenceHasDependentsError,
    EvidenceNotFoundError,
    create_evidence,
    delete_evidence,
    get_evidence,
    list_evidence,
    metadata_with_description,
    update_evidence,
)
from app.services.evidence_storage import EvidenceStorageError, delete_stored_file, save_upload

router = APIRouter(prefix="/api/evidence", tags=["evidence"])
DbSession = Annotated[Session, Depends(get_db)]


def _database_error() -> HTTPException:
    return HTTPException(status_code=500, detail="Database operation failed")


@router.post("/upload", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    db: DbSession,
    case_id: int = Form(gt=0),
    uploaded_file: UploadFile = File(...),
    description: str | None = Form(default=None, max_length=2000),
    evidence_type: EvidenceType = Form(default=EvidenceType.OTHER),
) -> EvidenceResponse:
    file_path: str | None = None
    try:
        file_path, file_name, _ = await save_upload(uploaded_file)
        await uploaded_file.seek(0)
        digest = hashlib.sha256()
        while chunk := await uploaded_file.read(1024 * 1024):
            digest.update(chunk)
        return create_evidence(
            db,
            case_id=case_id,
            evidence_type=evidence_type,
            file_name=file_name,
            file_path=file_path,
            mime_type=uploaded_file.content_type,
            file_hash=digest.hexdigest(),
            metadata_text=metadata_with_description(description, file_name),
        )
    except EvidenceStorageError as exc:
        if file_path:
            delete_stored_file(file_path)
        raise HTTPException(status_code=400, detail="Invalid or unsupported upload") from exc
    except EvidenceCaseNotFoundError as exc:
        if file_path:
            delete_stored_file(file_path)
        raise HTTPException(status_code=404, detail="Case not found") from exc
    except EvidenceDatabaseError as exc:
        if file_path:
            delete_stored_file(file_path)
        raise _database_error() from exc


@router.get("", response_model=EvidenceListResponse)
def get_evidence_list(
    db: DbSession,
    case_id: int | None = Query(default=None, gt=0),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> EvidenceListResponse:
    try:
        items, total = list_evidence(db, case_id=case_id, skip=skip, limit=limit)
        return EvidenceListResponse(items=list(items), total=total, skip=skip, limit=limit)
    except EvidenceDatabaseError as exc:
        raise _database_error() from exc


@router.get("/{evidence_id}", response_model=EvidenceResponse)
def get_evidence_item(evidence_id: int, db: DbSession) -> EvidenceResponse:
    try:
        return get_evidence(db, evidence_id)
    except EvidenceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Evidence not found") from exc
    except EvidenceDatabaseError as exc:
        raise _database_error() from exc


@router.put("/{evidence_id}", response_model=EvidenceResponse)
def update_evidence_item(evidence_id: int, payload: EvidenceUpdate, db: DbSession) -> EvidenceResponse:
    try:
        return update_evidence(db, evidence_id, payload.model_dump(exclude_unset=True))
    except EvidenceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Evidence not found") from exc
    except EvidenceDatabaseError as exc:
        raise _database_error() from exc


@router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_evidence(evidence_id: int, db: DbSession) -> Response:
    try:
        file_path = delete_evidence(db, evidence_id)
        delete_stored_file(file_path)
    except EvidenceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Evidence not found") from exc
    except EvidenceHasDependentsError as exc:
        raise HTTPException(status_code=409, detail="Evidence has dependent records and cannot be deleted safely") from exc
    except EvidenceStorageError as exc:
        raise HTTPException(status_code=500, detail="Stored evidence cleanup failed") from exc
    except EvidenceDatabaseError as exc:
        raise _database_error() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
