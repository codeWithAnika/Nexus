from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Identity, Integer, String, Text, Float, func
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
    source_relationships: Mapped[list["Relationship"]] = relationship(back_populates="source_entity", foreign_keys="Relationship.source_entity_id")
    target_relationships: Mapped[list["Relationship"]] = relationship(back_populates="target_entity", foreign_keys="Relationship.target_entity_id")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="entity")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="entity")