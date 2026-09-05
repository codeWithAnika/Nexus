from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class ReportBase(BaseModel):
    case_id: int = Field(..., description="Associated case ID")
    investigation_id: Optional[int] = Field(default=None, description="Optional investigation ID")
    report_type: str = Field(default="CRIMINAL_NETWORK_SUMMARY", max_length=100, description="Report type")
    title: str = Field(..., max_length=255, description="Report title")
    content: Optional[str] = Field(default=None, description="Generated markdown/text report content")


class ReportCreate(ReportBase):
    generated_by: Optional[int] = Field(default=1, description="User ID of author/generator")


class ReportResponse(ReportBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    generated_by: int
    created_at: datetime


class ReportListResponse(BaseModel):
    items: list[ReportResponse]
    total: int
    skip: int
    limit: int
