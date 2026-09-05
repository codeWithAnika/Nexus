from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.alert import AlertSeverity, AlertStatus


class AlertBase(BaseModel):
    case_id: int = Field(..., description="Associated case ID")
    entity_id: Optional[int] = Field(default=None, description="Triggering entity ID")
    analysis_id: Optional[int] = Field(default=None, description="Triggering analysis ID")
    alert_type: str = Field(..., max_length=100, description="Category of alert")
    severity: AlertSeverity = Field(default=AlertSeverity.MEDIUM, description="Alert severity level")
    title: str = Field(..., max_length=255, description="Alert headline")
    description: Optional[str] = Field(default=None, description="Detailed explanation of the risk/trigger")
    status: AlertStatus = Field(default=AlertStatus.OPEN, description="Workflow status")


class AlertCreate(AlertBase):
    pass


class AlertResponse(AlertBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    resolved_at: Optional[datetime] = None


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int
    skip: int
    limit: int
