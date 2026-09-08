"""
Data & Evidence Processing Package
SIH PS26189 - AI-Powered Criminal Network Analysis System
"""
from processing.schema import Entity, StructuredFIR
from processing.dataset_loader import load_and_group_fir_details
from processing.text_cleaner import clean_grouped_records
from processing.entity_extractor import extract_entities_for_records, derive_fir_id
from processing.deduplicator import deduplicate_entities

__all__ = [
    "Entity",
    "StructuredFIR",
    "load_and_group_fir_details",
    "clean_grouped_records",
    "extract_entities_for_records",
    "derive_fir_id",
    "deduplicate_entities",
]
