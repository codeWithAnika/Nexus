from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Identity, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class CaseStatus(str, Enum):
    OPEN = "OPEN"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    CLOSED = "CLOSED"


class CasePriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    case_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[CaseStatus] = mapped_column(SqlEnum(CaseStatus, native_enum=False, length=30), nullable=False, default=CaseStatus.OPEN)
    priority: Mapped[CasePriority] = mapped_column(SqlEnum(CasePriority, native_enum=False, length=10), nullable=False, default=CasePriority.MEDIUM)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    creator: Mapped["User"] = relationship(back_populates="cases")
    firs: Mapped[list["FIR"]] = relationship(back_populates="case")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="case")
    entities: Mapped[list["Entity"]] = relationship(back_populates="case")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="case")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="case")
    investigations: Mapped[list["Investigation"]] = relationship(back_populates="case")
    reports: Mapped[list["Report"]] = relationship(back_populates="case")