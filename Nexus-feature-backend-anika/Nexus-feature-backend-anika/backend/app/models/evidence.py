from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Identity, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class EvidenceType(str, Enum):
    FIR_DOCUMENT = "FIR_DOCUMENT"
    IMAGE = "IMAGE"
    OCR_TEXT = "OCR_TEXT"
    CDR = "CDR"
    TRANSACTION = "TRANSACTION"
    SURVEILLANCE = "SURVEILLANCE"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    INTELLIGENCE_REPORT = "INTELLIGENCE_REPORT"
    OTHER = "OTHER"


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), nullable=False)
    fir_id: Mapped[int | None] = mapped_column(ForeignKey("firs.id"))
    evidence_type: Mapped[EvidenceType] = mapped_column(SqlEnum(EvidenceType, native_enum=False, length=30), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255))
    file_path: Mapped[str | None] = mapped_column(String(500))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    file_hash: Mapped[str | None] = mapped_column(String(128))
    extracted_text: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(255))
    metadata_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False)

    case: Mapped["Case"] = relationship(back_populates="evidence")
    fir: Mapped["FIR | None"] = relationship(back_populates="evidence")
    identifiers: Mapped[list["EntityIdentifier"]] = relationship(back_populates="source_evidence")
    relationships: Mapped[list["Relationship"]] = relationship(back_populates="evidence")