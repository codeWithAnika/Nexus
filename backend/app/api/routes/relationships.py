from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.entity import Entity
from app.models.relationship import Relationship, RelationshipType
from app.schemas.relationship import RelationshipListResponse, RelationshipResponse

router = APIRouter(prefix="/api/relationships", tags=["relationships"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=RelationshipListResponse, status_code=status.HTTP_200_OK)
def list_relationships(
    db: DbSession,
    case_id: Optional[int] = Query(default=None, gt=0, description="Filter relationships by case ID"),
    entity_id: Optional[int] = Query(default=None, gt=0, description="Filter relationships connected to entity ID"),
    relationship_type: Optional[RelationshipType] = Query(default=None, description="Filter by relationship type"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> RelationshipListResponse:
    """Retrieve paginated relationships with optional filtering by case or entity."""
    query = select(Relationship)

    if case_id is not None:
        # Join entity to ensure relationships belong to case
        query = query.join(Entity, Relationship.source_entity_id == Entity.id).where(Entity.case_id == case_id)

    if entity_id is not None:
        query = query.where(
            (Relationship.source_entity_id == entity_id) | (Relationship.target_entity_id == entity_id)
        )

    if relationship_type is not None:
        query = query.where(Relationship.relationship_type == relationship_type)

    total_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(total_query) or 0

    items = db.scalars(query.offset(skip).limit(limit)).all()

    return RelationshipListResponse(
        items=[RelationshipResponse.model_validate(r) for r in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{relationship_id}", response_model=RelationshipResponse, status_code=status.HTTP_200_OK)
def get_relationship(relationship_id: int, db: DbSession) -> RelationshipResponse:
    """Retrieve a single relationship by ID."""
    rel = db.get(Relationship, relationship_id)
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return RelationshipResponse.model_validate(rel)
