from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.aayush_processing_adapter import AayushProcessingAdapter

router = APIRouter(prefix="/api/processing", tags=["processing"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/aayush-handoff", status_code=status.HTTP_200_OK)
def get_aayush_frozen_handoff() -> Dict[str, Any]:
    """
    Returns Aayush's processed evidence output mapped into the frozen standard handoff:
    {
      "entities": [...],
      "relationships": [...],
      "metadata": {...}
    }
    """
    try:
        return AayushProcessingAdapter.get_frozen_contract_handoff()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/cross-validate", status_code=status.HTTP_200_OK)
def cross_validate_processing(db: DbSession) -> Dict[str, Any]:
    """
    Cross-validates Aayush's processed evidence output against Oracle XE authoritative entities.
    Returns entity overlap, alignment rate, and distribution metrics.
    """
    try:
        return AayushProcessingAdapter.cross_validate(db)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
