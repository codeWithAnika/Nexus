from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.relationship import RelationshipType


class RelationshipBase(BaseModel):
    source_entity_id: int = Field(..., description="Source entity ID")
    target_entity_id: int = Field(..., description="Target entity ID")
    relationship_type: RelationshipType = Field(..., description="Category of relationship")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Confidence score")
    source_fir_id: Optional[int] = Field(default=None, description="Supporting FIR ID")
    evidence_id: Optional[int] = Field(default=None, description="Supporting evidence ID")
    description: Optional[str] = Field(default=None, description="Descriptive context or rule trigger")


class RelationshipCreate(RelationshipBase):
    pass


class RelationshipResponse(RelationshipBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class RelationshipListResponse(BaseModel):
    items: list[RelationshipResponse]
    total: int
    skip: int
    limit: int
