from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, Float, ForeignKey, Identity, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class EntityType(str, Enum):
    PERSON = "PERSON"
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    VEHICLE = "VEHICLE"
    LOCATION = "LOCATION"
    ORGANIZATION = "ORGANIZATION"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    TRANSACTION = "TRANSACTION"
    SOCIAL_MEDIA_ACCOUNT = "SOCIAL_MEDIA_ACCOUNT"
    CRIMINAL_CASE = "CRIMINAL_CASE"
    POLICE_STATION = "POLICE_STATION"
    STATUTE = "STATUTE"
    OTHER = "OTHER"


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), nullable=False)
    entity_type: Mapped[EntityType] = mapped_column(SqlEnum(EntityType, native_enum=False, length=30), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    case: Mapped["Case"] = relationship(back_populates="entities")
    identifiers: Mapped[list["EntityIdentifier"]] = relationship(back_populates="entity")
    mention_provenances: Mapped[list["EntityMentionProvenance"]] = relationship(back_populates="entity")
    source_relationships: Mapped[list["Relationship"]] = relationship(back_populates="source_entity", foreign_keys="Relationship.source_entity_id")
    target_relationships: Mapped[list["Relationship"]] = relationship(back_populates="target_entity", foreign_keys="Relationship.target_entity_id")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="entity")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="entity")


class EntityMentionProvenance(Base):
    __tablename__ = "entity_mention_provenance"
    __table_args__ = (
        UniqueConstraint("evidence_id", "source_index", "start_char", "end_char", name="uq_emp_mention"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), nullable=False)
    evidence_id: Mapped[int] = mapped_column(ForeignKey("evidence.id"), nullable=False)

    matched_text: Mapped[str] = mapped_column(String(500), nullable=False)
    start_char: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_char: Mapped[int | None] = mapped_column(Integer, nullable=True)

    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    extraction_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    final_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    low_ocr_confidence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    extraction_method: Mapped[str] = mapped_column(String(100), nullable=False)
    extractor_version: Mapped[str] = mapped_column(String(50), nullable=False)

    # ICDAR-specific provenance fields (nullable for generic evidence)
    source_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reconstructed_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_x1: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_y1: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_x2: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_y2: Mapped[float | None] = mapped_column(Float, nullable=True)
    original_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False)

    entity: Mapped["Entity"] = relationship(back_populates="mention_provenances")
    evidence: Mapped["Evidence"] = relationship()