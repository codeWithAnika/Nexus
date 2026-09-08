from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Identity, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class FIR(Base):
    __tablename__ = "firs"
    __table_args__ = (
        UniqueConstraint("dataset_image_id", name="uq_firs_dataset_image_id"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), nullable=False)
    fir_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    police_station: Mapped[str | None] = mapped_column(String(255))
    district: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    registration_date: Mapped[date | None] = mapped_column(Date)
    incident_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)
    source_file: Mapped[str | None] = mapped_column(String(500))
    # Anchors this row to FIR_Dataset_ICDAR2023 image_id (nullable for non-dataset FIRs)
    dataset_image_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False)

    case: Mapped["Case"] = relationship(back_populates="firs")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="fir")
    relationships: Mapped[list["Relationship"]] = relationship(back_populates="source_fir")