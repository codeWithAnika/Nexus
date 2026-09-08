"""
Pydantic schemas for the Data & Evidence Processing module.
Defines strict models for Entity and StructuredFIR.
"""
from typing import Any, List, Literal
from pydantic import BaseModel, ConfigDict, Field

# Strict category mapping as per system requirements:
# 0 -> LOCATION, 1 -> DATE, 2 -> CRIME TYPE, 3 -> PERSON
EntityType = Literal["LOCATION", "DATE", "CRIME TYPE", "PERSON"]


class Entity(BaseModel):
    """Represents an extracted entity with a unique identifier, mapped type, and cleaned value."""
    model_config = ConfigDict(strict=True, extra="forbid")

    id: str = Field(..., description="Unique entity identifier (e.g. P0001, L0001)")
    type: EntityType = Field(..., description="Entity category strictly mapped from dataset")
    value: str = Field(..., min_length=1, description="Cleaned and validated entity text value")


class StructuredFIR(BaseModel):
    """Represents a structured, validated FIR record containing extracted evidence."""
    model_config = ConfigDict(strict=True, extra="forbid")

    fir_id: str = Field(..., description="Clean FIR identifier derived from source image")
    source_image: str = Field(..., description="Original image filename from OCR dataset")
    entities: List[Entity] = Field(
        default_factory=list,
        description="Extracted and deduplicated entities for this FIR document"
    )
    relationships: List[Any] = Field(
        default_factory=list,
        description="Initial empty relationships list for downstream relationship extraction"
    )
