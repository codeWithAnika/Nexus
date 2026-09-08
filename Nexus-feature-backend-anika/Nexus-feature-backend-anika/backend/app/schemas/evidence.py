from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.evidence import EvidenceType


class EvidenceUpdate(BaseModel):
    evidence_type: EvidenceType | None = None
    description: str | None = Field(default=None, max_length=2000)
    source: str | None = Field(default=None, max_length=255)
    metadata_text: str | None = None


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    evidence_type: EvidenceType
    file_name: str | None
    mime_type: str | None
    file_hash: str | None
    source: str | None
    metadata_text: str | None
    created_at: datetime


class EvidenceListResponse(BaseModel):
    items: list[EvidenceResponse]
    total: int
    skip: int
    limit: int