from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, Float, ForeignKey, Identity, Integer, String, Text, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Analysis(Base):
    __tablename__ = "analyses"
    __table_args__ = (CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="ck_analysis_risk_score"),)

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(ForeignKey("entities.id"))
    source_evidence_id: Mapped[int | None] = mapped_column(ForeignKey("evidence.id"))
    analysis_type: Mapped[str] = mapped_column(String(100), nullable=False)
    risk_score: Mapped[float | None] = mapped_column(Float)
    risk_level: Mapped[RiskLevel | None] = mapped_column(SqlEnum(RiskLevel, native_enum=False, length=10))
    result_summary: Mapped[str | None] = mapped_column(Text)
    reasons: Mapped[str | None] = mapped_column(Text)
    model_version: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False)

    case: Mapped["Case"] = relationship(back_populates="analyses")
    entity: Mapped["Entity | None"] = relationship(back_populates="analyses")
    source_evidence: Mapped["Evidence | None"] = relationship()
    alerts: Mapped[list["Alert"]] = relationship(back_populates="analysis")