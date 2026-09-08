"""
Main pipeline execution script for Data & Evidence Processing module.
Coordinates ingestion, cleaning, extraction, deduplication, schema validation, and export.
"""
import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

# Ensure parent directory is in sys.path when running as a standalone script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from processing.dataset_loader import load_and_group_fir_details
from processing.text_cleaner import clean_grouped_records
from processing.entity_extractor import (
    EntityIDGenerator,
    derive_fir_id,
    extract_entities_for_records,
)
from processing.deduplicator import deduplicate_entities
from processing.schema import StructuredFIR


def run_pipeline(
    dataset_path: str = "FIR_details.json",
    output_path: str = "structured_evidence_output.json",
    min_score: float = 0.60,
    similarity_threshold: float = 90.0,
) -> List[StructuredFIR]:
    """Execute the end-to-end evidence processing pipeline."""
    print("=" * 60)
    print("SIH PS26189 - Data & Evidence Processing Pipeline")
    print("=" * 60)

    # 1. Ingestion & Grouping
    print("[1/5] Ingesting FIR_details.json and grouping by image...")
    grouped = load_and_group_fir_details(dataset_path)
    total_raw_records = sum(len(recs) for recs in grouped.values())
    print(f"      Loaded {len(grouped)} FIR images with {total_raw_records} raw OCR records.")

    # 2. Text Cleaning & Confidence Filtering (score >= 0.60)
    print(f"[2/5] Dropping OCR records with score < {min_score} and normalizing text...")
    cleaned_grouped = clean_grouped_records(grouped, min_score=min_score)
    total_cleaned_records = sum(len(recs) for recs in cleaned_grouped.values())
    dropped = total_raw_records - total_cleaned_records
    print(f"      Dropped {dropped} noisy records. {total_cleaned_records} records retained.")

    # 3. Entity Extraction & Category Mapping
    print("[3/5] Extracting mapped entities (0: LOCATION, 1: DATE, 2: CRIME TYPE, 3: PERSON)...")
    id_generator = EntityIDGenerator()
    unfiltered_extracted = 0
    raw_fir_entities: Dict[str, List[Any]] = {}

    for image_name, records in cleaned_grouped.items():
        ents = extract_entities_for_records(records, id_generator=id_generator)
        raw_fir_entities[image_name] = ents
        unfiltered_extracted += len(ents)

    # 4. Deduplication via rapidfuzz (>90% similarity)
    print(f"[4/5] Deduplicating entities per FIR with rapidfuzz (> {similarity_threshold}% threshold)...")
    structured_firs: List[StructuredFIR] = []
    total_deduped_entities = 0

    for image_name, ents in raw_fir_entities.items():
        clean_ents = deduplicate_entities(ents, similarity_threshold=similarity_threshold)
        total_deduped_entities += len(clean_ents)
        fir_id = derive_fir_id(image_name)

        # 5. Schema Validation against Pydantic StructuredFIR
        structured_fir = StructuredFIR(
            fir_id=fir_id,
            source_image=image_name,
            entities=clean_ents,
            relationships=[],
        )
        structured_firs.append(structured_fir)

    duplicates_removed = unfiltered_extracted - total_deduped_entities
    print(f"      Removed {duplicates_removed} duplicate entities.")
    print(f"      Total unique validated entities: {total_deduped_entities}.")

    # 6. Export to JSON
    out_file = Path(output_path)
    print(f"[5/5] Exporting {len(structured_firs)} validated FIR records to {out_file.name}...")
    export_data = [fir.model_dump() for fir in structured_firs]
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print("=" * 60)
    print(f"SUCCESS: Generated {out_file.resolve()}")
    print("=" * 60)
    return structured_firs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run FIR Evidence Processing Pipeline")
    parser.add_argument("--input", default="FIR_details.json", help="Path to FIR_details.json")
    parser.add_argument("--output", default="structured_evidence_output.json", help="Output JSON path")
    parser.add_argument("--min-score", type=float, default=0.60, help="Confidence threshold")
    parser.add_argument("--sim-threshold", type=float, default=90.0, help="Rapidfuzz similarity threshold")
    args = parser.parse_args()

    run_pipeline(
        dataset_path=args.input,
        output_path=args.output,
        min_score=args.min_score,
        similarity_threshold=args.sim_threshold,
    )


if __name__ == "__main__":
    main()
