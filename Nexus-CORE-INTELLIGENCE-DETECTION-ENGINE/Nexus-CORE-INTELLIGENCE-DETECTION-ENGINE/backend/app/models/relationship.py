from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Identity, Integer, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RelationshipType(str, Enum):
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    CALLED = "CALLED"
    TRANSFERRED_TO = "TRANSFERRED_TO"
    LOCATED_AT = "LOCATED_AT"
    OWNS = "OWNS"
    WORKS_FOR = "WORKS_FOR"
    RELATED_TO = "RELATED_TO"
    TRAVELED_WITH = "TRAVELED_WITH"
    COMMUNICATED_WITH = "COMMUNICATED_WITH"
    MEMBER_OF = "MEMBER_OF"
    MENTIONED_WITH = "MENTIONED_WITH"
    OTHER = "OTHER"


class Relationship(Base):
    __tablename__ = "relationships"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    source_entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), nullable=False)
    target_entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), nullable=False)
    relationship_type: Mapped[RelationshipType] = mapped_column(SqlEnum(RelationshipType, native_enum=False, length=30), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    source_fir_id: Mapped[int | None] = mapped_column(ForeignKey("firs.id"))
    evidence_id: Mapped[int | None] = mapped_column(ForeignKey("evidence.id"))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False)

    source_entity: Mapped["Entity"] = relationship(back_populates="source_relationships", foreign_keys=[source_entity_id])
    target_entity: Mapped["Entity"] = relationship(back_populates="target_relationships", foreign_keys=[target_entity_id])
    source_fir: Mapped["FIR | None"] = relationship(back_populates="relationships")
    evidence: Mapped["Evidence | None"] = relationship(back_populates="relationships")