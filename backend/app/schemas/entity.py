from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.entity import EntityType


def _required_text(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("must not be empty")
    return value


class EntityIdentifierCreate(BaseModel):
    identifier_type: str = Field(min_length=1, max_length=50)
    identifier_value: str = Field(min_length=1, max_length=500)
    normalized_value: str | None = Field(default=None, max_length=500)
    confidence: float | None = Field(default=None, ge=0, le=1)
    source_evidence_id: int | None = Field(default=None, gt=0)

    _validate_text = field_validator("identifier_type", "identifier_value")(_required_text)


class EntityIdentifierUpdate(BaseModel):
    identifier_type: str | None = Field(default=None, min_length=1, max_length=50)
    identifier_value: str | None = Field(default=None, min_length=1, max_length=500)
    normalized_value: str | None = Field(default=None, max_length=500)
    confidence: float | None = Field(default=None, ge=0, le=1)
    source_evidence_id: int | None = Field(default=None, gt=0)

    _validate_text = field_validator("identifier_type", "identifier_value")(_required_text)


class EntityCreate(BaseModel):
    case_id: int = Field(gt=0)
    entity_type: EntityType
    name: str = Field(min_length=1, max_length=255)
    normalized_name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)

    _validate_name = field_validator("name")(_required_text)


class EntityUpdate(BaseModel):
    entity_type: EntityType | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    normalized_name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)

    _validate_name = field_validator("name")(_required_text)


class EntityIdentifierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_id: int
    identifier_type: str
    identifier_value: str
    normalized_value: str | None
    confidence: float | None
    source_evidence_id: int | None
    created_at: datetime


class EntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    entity_type: EntityType
    name: str
    normalized_name: str | None
    description: str | None
    confidence: float | None
    created_at: datetime
    updated_at: datetime
    identifiers: list[EntityIdentifierResponse]


class EntityMentionProvenanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_id: int
    evidence_id: int
    matched_text: str
    start_char: int | None
    end_char: int | None
    ocr_confidence: float | None
    extraction_confidence: float
    final_confidence: float
    low_ocr_confidence: bool
    extraction_method: str
    extractor_version: str
    source_index: int | None
    reconstructed_order: int | None
    category_id: int | None
    bbox_x1: float | None
    bbox_y1: float | None
    bbox_x2: float | None
    bbox_y2: float | None
    original_text: str | None
    created_at: datetime


class EntityListResponse(BaseModel):
    items: list[EntityResponse]
    total: int
    skip: int
    limit: int