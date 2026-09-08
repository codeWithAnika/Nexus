from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Identity, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class EntityIdentifier(Base):
    __tablename__ = "entity_identifiers"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), nullable=False)
    identifier_type: Mapped[str] = mapped_column(String(50), nullable=False)
    identifier_value: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_value: Mapped[str | None] = mapped_column(String(500))
    confidence: Mapped[float | None] = mapped_column(Float)
    source_evidence_id: Mapped[int | None] = mapped_column(ForeignKey("evidence.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False)

    entity: Mapped["Entity"] = relationship(back_populates="identifiers")
    source_evidence: Mapped["Evidence | None"] = relationship(back_populates="identifiers")