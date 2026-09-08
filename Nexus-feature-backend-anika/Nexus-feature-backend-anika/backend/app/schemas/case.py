from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.case import CasePriority, CaseStatus


class CaseCreate(BaseModel):
    case_number: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: CaseStatus = CaseStatus.OPEN
    priority: CasePriority = CasePriority.MEDIUM
    created_by: int = Field(gt=0)


class CaseUpdate(BaseModel):
    case_number: str | None = Field(default=None, min_length=1, max_length=100)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: CaseStatus | None = None
    priority: CasePriority | None = None


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_number: str
    title: str
    description: str | None
    status: CaseStatus
    priority: CasePriority
    created_by: int
    created_at: datetime
    updated_at: datetime