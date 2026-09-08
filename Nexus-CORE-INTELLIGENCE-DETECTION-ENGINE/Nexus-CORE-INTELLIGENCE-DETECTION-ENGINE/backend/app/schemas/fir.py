from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _required_text(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("must not be empty")
    return value


class FIRCreate(BaseModel):
    case_id: int = Field(gt=0)
    fir_number: str = Field(min_length=1, max_length=100)
    police_station: str | None = Field(default=None, max_length=255)
    district: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    registration_date: date | None = None
    incident_date: date | None = None
    description: str | None = None
    # Original image filename from FIR_Dataset_ICDAR2023 (for provenance)
    source_file: str | None = Field(default=None, max_length=500)
    # Numeric image_id from FIR_Dataset_ICDAR2023; NULL for non-dataset FIRs
    dataset_image_id: int | None = Field(default=None, gt=0)

    _validate_fir_number = field_validator("fir_number")(_required_text)


class FIRUpdate(BaseModel):
    fir_number: str | None = Field(default=None, min_length=1, max_length=100)
    police_station: str | None = Field(default=None, max_length=255)
    district: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    registration_date: date | None = None
    incident_date: date | None = None
    description: str | None = None
    source_file: str | None = Field(default=None, max_length=500)
    dataset_image_id: int | None = Field(default=None, gt=0)

    _validate_fir_number = field_validator("fir_number")(_required_text)


class FIRResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    fir_number: str
    police_station: str | None
    district: str | None
    state: str | None
    registration_date: date | None
    incident_date: date | None
    description: str | None
    source_file: str | None
    dataset_image_id: int | None
    created_at: datetime


class FIRListResponse(BaseModel):
    items: list[FIRResponse]
    total: int
    skip: int
    limit: int
