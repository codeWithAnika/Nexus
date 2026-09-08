from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class ImportStatus(StrEnum):
    PROPOSED = "PROPOSED"
    IMPORTED = "IMPORTED"
    ALREADY_IMPORTED = "ALREADY_IMPORTED"
    RESUMED = "RESUMED"
    CONFLICT = "CONFLICT"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"


@dataclass(frozen=True)
class OCRInput:
    source_index: int
    image_id: int
    image_name: str
    bbox: tuple[float, float, float, float]
    score: float
    category_id: int
    text: str


@dataclass(frozen=True)
class AnnotatedImage:
    image_id: int
    image_name: str
    path: Path
    records: tuple[OCRInput, ...]


@dataclass(frozen=True)
class OCRToken:
    source_index: int
    bbox: tuple[float, float, float, float]
    score: float
    category_id: int
    original_text: str
    normalized_text: str
    height: float
    vertical_center: float
    reconstructed_order: int = -1


@dataclass(frozen=True)
class OCRReconstruction:
    extracted_text: str
    records: tuple[OCRToken, ...]


@dataclass(frozen=True)
class PreflightReport:
    dataset_root: Path
    json_path: Path
    image_count_on_disk: int
    annotated_image_count: int
    ocr_record_count: int
    unreferenced_images: tuple[str, ...]
    category_distribution: dict[int, int]
    score_min: float | None
    score_max: float | None
    duplicate_ocr_records: int
    suspicious_records: tuple[str, ...]
    filename_patterns: dict[str, int]
    images: tuple[AnnotatedImage, ...]


@dataclass(frozen=True)
class HandoffRecord:
    fir_id: int | None
    evidence_id: int | None
    dataset_image_id: int
    image_name: str
    extracted_text: str
    provenance: dict[str, Any]


@dataclass
class ImageResult:
    image_id: int
    image_name: str
    status: ImportStatus
    reason: str | None = None


@dataclass
class ImportReport:
    total_annotated_images: int
    imported: int = 0
    already_imported: int = 0
    resumed: int = 0
    conflicts: int = 0
    failed: int = 0
    quarantined: int = 0
    unreferenced_images: int = 0
    results: list[ImageResult] = field(default_factory=list)
    handoff: list[HandoffRecord] = field(default_factory=list)

    def add(self, result: ImageResult) -> None:
        self.results.append(result)
        counters = {
            ImportStatus.IMPORTED: "imported",
            ImportStatus.ALREADY_IMPORTED: "already_imported",
            ImportStatus.RESUMED: "resumed",
            ImportStatus.CONFLICT: "conflicts",
            ImportStatus.FAILED: "failed",
            ImportStatus.QUARANTINED: "quarantined",
        }
        counter_name = counters.get(result.status)
        if counter_name:
            setattr(self, counter_name, getattr(self, counter_name) + 1)
