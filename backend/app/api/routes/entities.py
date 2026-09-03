from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.entity import EntityType
from app.schemas.entity import (
    EntityCreate,
    EntityIdentifierCreate,
    EntityIdentifierResponse,
    EntityIdentifierUpdate,
    EntityListResponse,
    EntityResponse,
    EntityUpdate,
)
from app.services.entity_service import (
    EntityCaseNotFoundError,
    EntityDatabaseError,
    EntityHasDependentsError,
    EntityIdentifierEvidenceNotFoundError,
    EntityIdentifierNotFoundError,
    EntityNotFoundError,
    create_entity,
    create_identifier,
    delete_entity,
    delete_identifier,
    get_entity,
    list_entities,
    list_identifiers,
    update_entity,
    update_identifier,
)

router = APIRouter(prefix="/api/entities", tags=["entities"])
DbSession = Annotated[Session, Depends(get_db)]


def _database_error() -> HTTPException:
    return HTTPException(status_code=500, detail="Database operation failed")


def _entity_not_found(exc: Exception) -> HTTPException:
    return HTTPException(status_code=404, detail="Entity not found")


@router.post("", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
def create_entity_endpoint(payload: EntityCreate, db: DbSession) -> EntityResponse:
    try:
        return create_entity(db, payload.model_dump())
    except EntityCaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc
    except EntityDatabaseError as exc:
        raise _database_error() from exc


@router.get("", response_model=EntityListResponse)
def get_entity_list(
    db: DbSession,
    case_id: int | None = Query(default=None, gt=0),
    entity_type: EntityType | None = None,
    normalized_name: str | None = Query(default=None, min_length=1, max_length=255),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> EntityListResponse:
    try:
        items, total = list_entities(db, case_id=case_id, entity_type=entity_type, normalized_name=normalized_name, skip=skip, limit=limit)
        return EntityListResponse(items=list(items), total=total, skip=skip, limit=limit)
    except EntityDatabaseError as exc:
        raise _database_error() from exc


@router.post("/{entity_id}/identifiers", response_model=EntityIdentifierResponse, status_code=status.HTTP_201_CREATED)
def add_identifier(entity_id: int, payload: EntityIdentifierCreate, db: DbSession) -> EntityIdentifierResponse:
    try:
        return create_identifier(db, entity_id, payload.model_dump())
    except EntityNotFoundError as exc:
        raise _entity_not_found(exc)
    except EntityIdentifierEvidenceNotFoundError as exc:
        raise HTTPException(status_code=400, detail="Source evidence not found in the entity case") from exc
    except EntityDatabaseError as exc:
        raise _database_error() from exc


@router.get("/{entity_id}/identifiers", response_model=list[EntityIdentifierResponse])
def get_identifiers(entity_id: int, db: DbSession) -> list[EntityIdentifierResponse]:
    try:
        return list(list_identifiers(db, entity_id))
    except EntityNotFoundError as exc:
        raise _entity_not_found(exc)
    except EntityDatabaseError as exc:
        raise _database_error() from exc


@router.put("/{entity_id}/identifiers/{identifier_id}", response_model=EntityIdentifierResponse)
def edit_identifier(entity_id: int, identifier_id: int, payload: EntityIdentifierUpdate, db: DbSession) -> EntityIdentifierResponse:
    try:
        return update_identifier(db, entity_id, identifier_id, payload.model_dump(exclude_unset=True))
    except EntityNotFoundError as exc:
        raise _entity_not_found(exc)
    except EntityIdentifierNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Entity identifier not found") from exc
    except EntityIdentifierEvidenceNotFoundError as exc:
        raise HTTPException(status_code=400, detail="Source evidence not found in the entity case") from exc
    except EntityDatabaseError as exc:
        raise _database_error() from exc


@router.delete("/{entity_id}/identifiers/{identifier_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_identifier(entity_id: int, identifier_id: int, db: DbSession) -> Response:
    try:
        delete_identifier(db, entity_id, identifier_id)
    except EntityNotFoundError as exc:
        raise _entity_not_found(exc)
    except EntityIdentifierNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Entity identifier not found") from exc
    except EntityDatabaseError as exc:
        raise _database_error() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{entity_id}", response_model=EntityResponse)
def get_entity_item(entity_id: int, db: DbSession) -> EntityResponse:
    try:
        return get_entity(db, entity_id)
    except EntityNotFoundError as exc:
        raise _entity_not_found(exc)
    except EntityDatabaseError as exc:
        raise _database_error() from exc


@router.put("/{entity_id}", response_model=EntityResponse)
def edit_entity(entity_id: int, payload: EntityUpdate, db: DbSession) -> EntityResponse:
    try:
        return update_entity(db, entity_id, payload.model_dump(exclude_unset=True))
    except EntityNotFoundError as exc:
        raise _entity_not_found(exc)
    except EntityDatabaseError as exc:
        raise _database_error() from exc


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_entity(entity_id: int, db: DbSession) -> Response:
    try:
        delete_entity(db, entity_id)
    except EntityNotFoundError as exc:
        raise _entity_not_found(exc)
    except EntityHasDependentsError as exc:
        raise HTTPException(status_code=409, detail="Entity has dependent records and cannot be deleted safely") from exc
    except EntityDatabaseError as exc:
        raise _database_error() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)