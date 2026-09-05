from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ExtractionEntityType(StrEnum):
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    POLICE_STATION = "POLICE_STATION"
    STATUTE = "STATUTE"
    IDENTIFIER = "IDENTIFIER"
    OTHER = "OTHER"


@dataclass(frozen=True)
class TextSpan:
    start_char: int
    end_char: int
    matched_text: str

    def validate(self, original_text: str) -> bool:
        if self.start_char < 0 or self.end_char > len(original_text) or self.start_char >= self.end_char:
            return False
        return original_text[self.start_char:self.end_char] == self.matched_text


@dataclass(frozen=True)
class IdentifierCandidate:
    identifier_type: str
    identifier_value: str
    normalized_value: str | None = None
    confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "identifier_type": self.identifier_type,
            "identifier_value": self.identifier_value,
            "normalized_value": self.normalized_value,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class CandidateProvenance:
    dataset_name: str
    dataset_image_id: int
    image_name: str
    fir_id: int
    fir_number: str
    source_evidence_id: int
    source_index: int
    reconstructed_order: int
    bbox: tuple[float, float, float, float]
    ocr_score: float
    category_id: int
    original_text: str
    span: TextSpan

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "dataset_image_id": self.dataset_image_id,
            "image_name": self.image_name,
            "fir_id": self.fir_id,
            "fir_number": self.fir_number,
            "source_evidence_id": self.source_evidence_id,
            "source_index": self.source_index,
            "reconstructed_order": self.reconstructed_order,
            "bbox": list(self.bbox),
            "ocr_score": self.ocr_score,
            "category_id": self.category_id,
            "original_text": self.original_text,
            "span": {
                "start_char": self.span.start_char,
                "end_char": self.span.end_char,
                "matched_text": self.span.matched_text,
            },
        }


@dataclass(frozen=True)
class EntityCandidate:
    temp_id: str
    case_id: int
    fir_id: int
    dataset_image_id: int
    source_evidence_id: int
    extraction_entity_type: ExtractionEntityType
    raw_value: str
    normalized_value: str
    ocr_confidence: float
    extraction_confidence: float
    entity_confidence: float
    low_ocr_confidence: bool
    extraction_method: str
    provenance: CandidateProvenance
    identifiers: tuple[IdentifierCandidate, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "temp_id": self.temp_id,
            "case_id": self.case_id,
            "fir_id": self.fir_id,
            "dataset_image_id": self.dataset_image_id,
            "source_evidence_id": self.source_evidence_id,
            "extraction_entity_type": self.extraction_entity_type.value,
            "raw_value": self.raw_value,
            "normalized_value": self.normalized_value,
            "ocr_confidence": self.ocr_confidence,
            "extraction_confidence": self.extraction_confidence,
            "entity_confidence": self.entity_confidence,
            "low_ocr_confidence": self.low_ocr_confidence,
            "extraction_method": self.extraction_method,
            "provenance": self.provenance.to_dict(),
            "identifiers": [ident.to_dict() for ident in self.identifiers],
        }


@dataclass
class PilotExtractionReport:
    pilot_image_ids: tuple[int, ...]
    total_images_processed: int
    ocr_records_processed: int
    candidates_extracted: int
    candidates_by_type: dict[str, int] = field(default_factory=dict)
    candidates_by_category: dict[int, int] = field(default_factory=dict)
    low_ocr_confidence_count: int = 0
    duplicate_mentions_preserved: int = 0
    unsupported_db_taxonomy_count: int = 0
    per_image_summary: list[dict[str, Any]] = field(default_factory=list)
    rejections: list[dict[str, Any]] = field(default_factory=list)
    relationships_count: int = 0
    entity_resolution_performed: bool = False
    database_migrations_created: bool = False
    raw_dataset_modified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "pilot_image_ids": list(self.pilot_image_ids),
            "total_images_processed": self.total_images_processed,
            "ocr_records_processed": self.ocr_records_processed,
            "candidates_extracted": self.candidates_extracted,
            "candidates_by_type": self.candidates_by_type,
            "candidates_by_category": self.candidates_by_category,
            "low_ocr_confidence_count": self.low_ocr_confidence_count,
            "duplicate_mentions_preserved": self.duplicate_mentions_preserved,
            "unsupported_db_taxonomy_count": self.unsupported_db_taxonomy_count,
            "per_image_summary": self.per_image_summary,
            "rejections": self.rejections,
            "relationships_count": self.relationships_count,
            "entity_resolution_performed": self.entity_resolution_performed,
            "database_migrations_created": self.database_migrations_created,
            "raw_dataset_modified": self.raw_dataset_modified,
        }
