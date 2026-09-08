from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.schemas.alert import AlertListResponse, AlertResponse

router = APIRouter(prefix="/api/alerts", tags=["alerts"])
DbSession = Annotated[Session, Depends(get_db)]


class AlertStatusUpdate(BaseModel):
    status: AlertStatus


@router.get("", response_model=AlertListResponse, status_code=status.HTTP_200_OK)
def list_alerts(
    db: DbSession,
    case_id: Optional[int] = Query(default=None, gt=0, description="Filter alerts by case ID"),
    severity: Optional[AlertSeverity] = Query(default=None, description="Filter by alert severity"),
    status_filter: Optional[AlertStatus] = Query(default=None, alias="status", description="Filter by status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> AlertListResponse:
    """Retrieve paginated alerts with optional filtering."""
    query = select(Alert)

    if case_id is not None:
        query = query.where(Alert.case_id == case_id)

    if severity is not None:
        query = query.where(Alert.severity == severity)

    if status_filter is not None:
        query = query.where(Alert.status == status_filter)

    total_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(total_query) or 0

    items = db.scalars(query.order_by(Alert.id.desc()).offset(skip).limit(limit)).all()

    return AlertListResponse(
        items=[AlertResponse.model_validate(a) for a in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{alert_id}", response_model=AlertResponse, status_code=status.HTTP_200_OK)
def get_alert(alert_id: int, db: DbSession) -> AlertResponse:
    """Retrieve a single alert by ID."""
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse.model_validate(alert)


@router.put("/{alert_id}/status", response_model=AlertResponse, status_code=status.HTTP_200_OK)
def update_alert_status(alert_id: int, payload: AlertStatusUpdate, db: DbSession) -> AlertResponse:
    """Update alert status (e.g. ACKNOWLEDGED, RESOLVED)."""
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = payload.status
    if payload.status == AlertStatus.RESOLVED:
        alert.resolved_at = datetime.now(timezone.utc)
    else:
        alert.resolved_at = None

    db.commit()
    db.refresh(alert)
    return AlertResponse.model_validate(alert)
