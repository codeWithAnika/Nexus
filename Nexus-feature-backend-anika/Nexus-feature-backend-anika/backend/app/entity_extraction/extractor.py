from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.entity_extraction.config import DEFAULT_CONFIG, PILOT_IMAGE_IDS, VALIDATION_BATCH_IMAGE_IDS, ExtractionConfig
from app.entity_extraction.models import (
    CandidateProvenance,
    EntityCandidate,
    ExtractionEntityType,
    PilotExtractionReport,
)
from app.entity_extraction.rules import (
    extract_from_category_0,
    extract_from_category_1,
    extract_from_category_2,
    extract_from_category_3,
)
from app.models.entity import EntityType
from app.models.evidence import Evidence
from app.models.fir import FIR


class PilotScopeError(ValueError):
    pass


def extract_batch_entities(
    *,
    db: Session,
    config: ExtractionConfig = DEFAULT_CONFIG,
    requested_image_ids: set[int] | None = None,
    allowed_scope: frozenset[int] = VALIDATION_BATCH_IMAGE_IDS,
) -> tuple[dict[str, Any], PilotExtractionReport]:
    target_ids = requested_image_ids if requested_image_ids is not None else allowed_scope
    # Hard safety guard: refuse to process any image ID outside approved scope
    invalid_ids = set(target_ids) - allowed_scope
    if invalid_ids:
        raise PilotScopeError(f"Safety guard: requested image IDs {sorted(invalid_ids)} are outside approved scope {sorted(allowed_scope)}")


    sorted_target_ids = sorted(target_ids)
    all_candidates: list[EntityCandidate] = []
    report = PilotExtractionReport(
        pilot_image_ids=tuple(sorted_target_ids),
        total_images_processed=0,
        ocr_records_processed=0,
        candidates_extracted=0,
    )

    supported_db_types = {e.value for e in EntityType}

    candidate_counter = 0

    for img_id in sorted_target_ids:
        fir = db.scalar(select(FIR).where(FIR.dataset_image_id == img_id))
        if not fir:
            report.rejections.append({
                "dataset_image_id": img_id,
                "reason": f"FIR record not found for dataset_image_id={img_id}",
            })
            continue

        evidence = db.scalar(select(Evidence).where(Evidence.fir_id == fir.id, Evidence.case_id == fir.case_id))
        if not evidence or not evidence.metadata_text:
            report.rejections.append({
                "dataset_image_id": img_id,
                "reason": f"Evidence not found or missing metadata_text for FIR id={fir.id}",
            })
            continue

        try:
            metadata = json.loads(evidence.metadata_text)
        except json.JSONDecodeError as exc:
            report.rejections.append({
                "dataset_image_id": img_id,
                "reason": f"Corrupt metadata_text JSON for Evidence id={evidence.id}: {exc}",
            })
            continue

        ocr_records = metadata.get("ocr_records", [])
        report.ocr_records_processed += len(ocr_records)
        report.total_images_processed += 1

        img_candidates: list[EntityCandidate] = []
        img_seen_names: dict[str, int] = defaultdict(int)

        for record in ocr_records:
            cat_id = record.get("category_id")
            original_text = record.get("original_text", "")
            ocr_score = float(record.get("score", 0.0))
            source_index = int(record.get("source_index", -1))
            reconstructed_order = int(record.get("reconstructed_order", -1))
            bbox = tuple(record.get("bbox", (0.0, 0.0, 0.0, 0.0)))

            # Category-specific extraction
            if cat_id == 0:
                span_candidates = extract_from_category_0(original_text)
            elif cat_id == 1:
                span_candidates = extract_from_category_1(original_text)
            elif cat_id == 2:
                span_candidates = extract_from_category_2(original_text)
            elif cat_id == 3:
                span_candidates = extract_from_category_3(original_text)
            else:
                span_candidates = []

            for sc in span_candidates:
                # Validate span against original_text
                if not sc.span.validate(original_text):
                    report.rejections.append({
                        "dataset_image_id": img_id,
                        "source_index": source_index,
                        "reason": f"Span mismatch: '{sc.span.matched_text}' not at [{sc.span.start_char}:{sc.span.end_char}] in '{original_text}'",
                    })
                    continue

                candidate_counter += 1
                temp_id = f"cand_pilot_{candidate_counter:03d}"

                low_ocr = ocr_score < config.low_ocr_threshold
                if low_ocr:
                    report.low_ocr_confidence_count += 1

                entity_conf = config.compute_entity_confidence(ocr_score, sc.extraction_confidence)

                provenance = CandidateProvenance(
                    dataset_name=config.dataset_name,
                    dataset_image_id=img_id,
                    image_name=metadata.get("image_name", ""),
                    fir_id=fir.id,
                    fir_number=fir.fir_number,
                    source_evidence_id=evidence.id,
                    source_index=source_index,
                    reconstructed_order=reconstructed_order,
                    bbox=bbox,
                    ocr_score=ocr_score,
                    category_id=cat_id,
                    original_text=original_text,
                    span=sc.span,
                )

                cand = EntityCandidate(
                    temp_id=temp_id,
                    case_id=fir.case_id,
                    fir_id=fir.id,
                    dataset_image_id=img_id,
                    source_evidence_id=evidence.id,
                    extraction_entity_type=sc.entity_type,
                    raw_value=sc.raw_value,
                    normalized_value=sc.normalized_value,
                    ocr_confidence=ocr_score,
                    extraction_confidence=sc.extraction_confidence,
                    entity_confidence=entity_conf,
                    low_ocr_confidence=low_ocr,
                    extraction_method=sc.extraction_method,
                    provenance=provenance,
                    identifiers=sc.identifiers,
                )

                img_candidates.append(cand)
                all_candidates.append(cand)

                # Check duplicate mentions in this image
                img_seen_names[sc.raw_value] += 1
                if img_seen_names[sc.raw_value] > 1:
                    report.duplicate_mentions_preserved += 1

                # Check supported DB taxonomy
                if sc.entity_type.value not in supported_db_types:
                    report.unsupported_db_taxonomy_count += 1

                # Counts
                report.candidates_by_type[sc.entity_type.value] = report.candidates_by_type.get(sc.entity_type.value, 0) + 1
                report.candidates_by_category[cat_id] = report.candidates_by_category.get(cat_id, 0) + 1

        report.per_image_summary.append({
            "dataset_image_id": img_id,
            "fir_id": fir.id,
            "fir_number": fir.fir_number,
            "ocr_records_count": len(ocr_records),
            "candidates_count": len(img_candidates),
            "candidates": [c.temp_id for c in img_candidates],
        })

    report.candidates_extracted = len(all_candidates)

    handoff = {
        "entities": [c.to_dict() for c in all_candidates],
        "relationships": [],
        "metadata": {
            "extractor_version": config.extractor_version,
            "dataset_name": config.dataset_name,
            "pilot_mode": True,
            "pilot_image_ids": sorted_target_ids,
            "confidence_formula": f"{config.w_ocr}*C_ocr + {config.w_ext}*C_ext",
            "total_candidates": len(all_candidates),
            "total_images_processed": report.total_images_processed,
            "total_ocr_records_processed": report.ocr_records_processed,
            "low_ocr_confidence_count": report.low_ocr_confidence_count,
            "duplicate_mentions_preserved": report.duplicate_mentions_preserved,
            "unsupported_db_taxonomy_count": report.unsupported_db_taxonomy_count,
        },
    }

    return handoff, report


def extract_pilot_entities(
    *,
    db: Session,
    config: ExtractionConfig = DEFAULT_CONFIG,
    requested_image_ids: set[int] | None = None,
) -> tuple[dict[str, Any], PilotExtractionReport]:
    return extract_batch_entities(
        db=db,
        config=config,
        requested_image_ids=requested_image_ids,
        allowed_scope=PILOT_IMAGE_IDS,
    )
