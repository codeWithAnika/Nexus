from __future__ import annotations

from dataclasses import dataclass

PILOT_IMAGE_IDS = frozenset({0, 1, 2, 3, 4})
VALIDATION_BATCH_IMAGE_IDS = frozenset(range(25))
FULL_DATASET_IMAGE_IDS = frozenset(range(569))
DATASET_NAME = "FIR_Dataset_ICDAR2023"
EXTRACTOR_VERSION = "2.1.0-pilot"


@dataclass(frozen=True)
class ExtractionConfig:
    w_ocr: float = 0.30
    w_ext: float = 0.70
    low_ocr_threshold: float = 0.60
    dataset_name: str = DATASET_NAME
    extractor_version: str = EXTRACTOR_VERSION

    def compute_entity_confidence(self, ocr_confidence: float, extraction_confidence: float) -> float:
        score = (self.w_ocr * ocr_confidence) + (self.w_ext * extraction_confidence)
        return round(min(1.0, max(0.0, score)), 4)


DEFAULT_CONFIG = ExtractionConfig()
