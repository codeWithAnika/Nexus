"""
Entity extraction and category mapping module.
Maps category_id:
  0 -> LOCATION
  1 -> DATE
  2 -> CRIME TYPE
  3 -> PERSON
Generates unique IDs and derives clean fir_id from image_name.
"""
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
import dateparser
import spacy

from processing.schema import Entity, EntityType

# Category mapping strictly adhering to specifications
CATEGORY_MAPPING: Dict[int, EntityType] = {
    0: "LOCATION",
    1: "DATE",
    2: "CRIME TYPE",
    3: "PERSON",
}

# Prefix mapping for readable, standardized entity IDs
PREFIX_MAPPING: Dict[EntityType, str] = {
    "PERSON": "P",
    "LOCATION": "L",
    "DATE": "D",
    "CRIME TYPE": "C",
}

# Load spaCy pipeline for linguistic refinement
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = spacy.blank("en")


def derive_fir_id(image_name: str) -> str:
    """
    Derive a clean FIR ID from image_name.
    Strips image extension (.jpg, .png) and page suffix (__1, __2).
    E.g. 'Airport PSAIRPORT-0004-2017-2711__1.jpg' -> 'Airport PSAIRPORT-0004-2017-2711'
    """
    stem = Path(image_name).stem
    clean = re.sub(r'__\d+$', '', stem)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def refine_entity_value(category: EntityType, value: str) -> str:
    """Validate and refine entity values using dateparser and spacy."""
    val = value.strip()
    if category == "DATE":
        # Validate date format using dateparser
        parsed = dateparser.parse(val)
        if parsed:
            # If 4-digit year, preserve it; otherwise standard ISO date string
            if re.fullmatch(r'\d{4}', val):
                return val
            return parsed.strftime("%Y-%m-%d")
        return val

    if category in ("PERSON", "LOCATION"):
        # Use spaCy for linguistic token cleanup if needed
        doc = nlp(val)
        tokens = [token.text for token in doc if not token.is_space]
        return " ".join(tokens) if tokens else val

    return val


class EntityIDGenerator:
    """Generates unique sequential entity IDs across the pipeline (e.g. P0001, L0001)."""

    def __init__(self) -> None:
        self.counters: Dict[str, int] = {
            "P": 0,
            "L": 0,
            "D": 0,
            "C": 0,
        }

    def generate_id(self, entity_type: EntityType) -> str:
        prefix = PREFIX_MAPPING[entity_type]
        self.counters[prefix] += 1
        return f"{prefix}{self.counters[prefix]:04d}"


def extract_entities_for_records(
    records: List[Dict[str, Any]],
    id_generator: Optional[EntityIDGenerator] = None
) -> List[Entity]:
    """
    Extract and map entities from filtered OCR records.
    Ensures strict adherence to the 4 permitted categories and assigns unique IDs.
    """
    if id_generator is None:
        id_generator = EntityIDGenerator()

    entities: List[Entity] = []
    for record in records:
        cat_id = record.get("category_id")
        if cat_id not in CATEGORY_MAPPING:
            continue  # Do not invent categories outside the mapping

        entity_type = CATEGORY_MAPPING[cat_id]
        raw_val = record.get("text", "")
        refined_val = refine_entity_value(entity_type, raw_val)

        if not refined_val:
            continue

        entity_id = id_generator.generate_id(entity_type)
        entities.append(
            Entity(
                id=entity_id,
                type=entity_type,
                value=refined_val,
            )
        )

    return entities
