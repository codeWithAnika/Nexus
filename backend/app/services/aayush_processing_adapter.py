"""
Aayush Processing Adapter
Bridges Aayush's Evidence Processing pipeline (PS189) with the Nexus Backend.
Converts Aayush's StructuredFIR output into the frozen contract:
{
  "entities": [],
  "relationships": [],
  "metadata": {}
}
and provides cross-validation metrics against Oracle XE authoritative entities.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entity import Entity, EntityType
from app.models.fir import FIR

logger = logging.getLogger(__name__)


def _find_aayush_structured_output() -> Optional[Path]:
    """Search for structured_evidence_output.json across known teammate directories."""
    candidate_paths = [
        Path(__file__).resolve().parent.parent.parent.parent / "aayush work" / "PS189" / "structured_evidence_output.json",
        Path(__file__).resolve().parent.parent.parent / "storage" / "structured_evidence_output.json",
        Path(r"C:\Users\anika\.gemini\antigravity\brain\318c5340-7670-4f40-936e-0cc42bdfda50\scratch\aayush\PS189\structured_evidence_output.json"),
    ]
    for p in candidate_paths:
        if p.exists():
            return p
    return None


class AayushProcessingAdapter:
    """Adapter bridging Aayush's processing artifacts to backend standard format."""

    @staticmethod
    def load_aayush_structured_data() -> List[Dict[str, Any]]:
        """Loads Aayush's structured evidence JSON output."""
        path = _find_aayush_structured_output()
        if not path or not path.exists():
            raise FileNotFoundError("Could not find Aayush's structured_evidence_output.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def get_frozen_contract_handoff(cls) -> Dict[str, Any]:
        """
        Transforms Aayush's StructuredFIR list into the frozen handoff contract:
        {
          "entities": [],
          "relationships": [],
          "metadata": {}
        }
        """
        raw_firs = cls.load_aayush_structured_data()
        standard_entities: List[Dict[str, Any]] = []

        # Type mapping from Aayush schema to Backend EntityType
        type_map = {
            "LOCATION": "POLICE_STATION",
            "CRIME TYPE": "STATUTE",
            "PERSON": "PERSON",
            "DATE": None,  # Metadata only; not a canonical graph entity
        }

        for fir in raw_firs:
            fir_id_str = fir.get("fir_id", "")
            # Derive numeric image_id if possible (e.g. FIR_0 -> 0)
            img_id = None
            if fir_id_str.startswith("FIR_"):
                try:
                    img_id = int(fir_id_str.replace("FIR_", ""))
                except ValueError:
                    pass

            for ent in fir.get("entities", []):
                mapped_type = type_map.get(ent.get("type"))
                if not mapped_type:
                    continue  # Skip DATE or unmapped types

                standard_entities.append({
                    "temp_id": ent.get("id"),
                    "fir_id_ref": fir_id_str,
                    "dataset_image_id": img_id,
                    "extraction_entity_type": mapped_type,
                    "raw_value": ent.get("value"),
                    "normalized_value": ent.get("value", "").strip(),
                    "source_image": fir.get("source_image"),
                    "provenance": {
                        "source": "aayush_processing",
                        "fir_id": fir_id_str,
                        "original_type": ent.get("type"),
                    },
                })

        return {
            "entities": standard_entities,
            "relationships": [],
            "metadata": {
                "source": "aayush_processing",
                "processor_version": "1.0.0",
                "total_firs_processed": len(raw_firs),
                "total_entities_extracted": len(standard_entities),
            },
        }

    @classmethod
    def cross_validate(cls, db: Session) -> Dict[str, Any]:
        """
        Cross-validates Aayush's processed evidence output against Oracle XE authoritative entities.
        Computes coverage, entity overlap, and alignment metrics.
        """
        handoff = cls.get_frozen_contract_handoff()
        aayush_entities = handoff["entities"]

        # Oracle authoritative entities
        oracle_entities = list(db.scalars(select(Entity)).all())
        oracle_names_by_type: Dict[str, Set[str]] = {
            "PERSON": set(),
            "POLICE_STATION": set(),
            "STATUTE": set(),
        }
        for e in oracle_entities:
            t = e.entity_type.value if hasattr(e.entity_type, "value") else str(e.entity_type)
            if t in oracle_names_by_type:
                oracle_names_by_type[t].add(e.normalized_name.lower())

        # Check overlap
        matched_count = 0
        unmatched_count = 0
        overlap_by_type = {"PERSON": 0, "POLICE_STATION": 0, "STATUTE": 0}

        for ae in aayush_entities:
            etype = ae["extraction_entity_type"]
            val = ae["normalized_value"].lower()
            if etype in oracle_names_by_type and val in oracle_names_by_type[etype]:
                matched_count += 1
                overlap_by_type[etype] += 1
            else:
                unmatched_count += 1

        total_aayush = len(aayush_entities)
        match_rate = (matched_count / total_aayush * 100.0) if total_aayush > 0 else 0.0

        return {
            "aayush_total_firs": handoff["metadata"]["total_firs_processed"],
            "aayush_total_entities": total_aayush,
            "oracle_total_canonical_entities": len(oracle_entities),
            "matched_entities_count": matched_count,
            "unmatched_entities_count": unmatched_count,
            "match_rate_percent": round(match_rate, 2),
            "overlap_by_type": overlap_by_type,
            "alignment_verdict": "STRONG_CORROBORATION" if match_rate > 70.0 else "PARTIAL_ALIGNMENT",
            "notes": (
                "Aayush's processor applies strict confidence filtering (score >= 0.60) "
                "and rapidfuzz deduplication (>90%). Authoritative backend preserves raw "
                "character spans and bounding boxes in entity_mention_provenance."
            ),
        }
