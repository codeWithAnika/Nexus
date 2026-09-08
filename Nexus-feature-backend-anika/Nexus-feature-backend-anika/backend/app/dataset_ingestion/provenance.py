import json
from typing import Any

from app.dataset_ingestion.config import DATASET_NAME
from app.dataset_ingestion.models import OCRReconstruction


def build_provenance(
    *,
    archive_sha256: str,
    dataset_image_id: int,
    image_name: str,
    image_sha256: str,
    reconstruction: OCRReconstruction,
) -> dict[str, Any]:
    return {
        "dataset_name": DATASET_NAME,
        "archive_sha256": archive_sha256,
        "dataset_image_id": dataset_image_id,
        "image_name": image_name,
        "image_sha256": image_sha256,
        "ocr_record_count": len(reconstruction.records),
        "ocr_records": [
            {
                "source_index": record.source_index,
                "bbox": list(record.bbox),
                "score": record.score,
                "category_id": record.category_id,
                "original_text": record.original_text,
                "normalized_text": record.normalized_text,
                "reconstructed_order": record.reconstructed_order,
            }
            for record in reconstruction.records
        ],
    }


def provenance_text(provenance: dict[str, Any]) -> str:
    return json.dumps(provenance, ensure_ascii=True, separators=(",", ":"))
