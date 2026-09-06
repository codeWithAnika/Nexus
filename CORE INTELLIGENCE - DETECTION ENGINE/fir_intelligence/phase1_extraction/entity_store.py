"""
EntityStore output interface for Phase 1.
Provides a clean, queryable, and exportable interface consumed by Phase 2 (Relationship Mining).
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd

from .models import CandidateMerge, Entity, EntityType, MergeDecision


class EntityStore:
    """
    In-memory store and output interface for extracted, normalized,
    and deduplicated entities.
    """

    def __init__(
        self,
        entities: Optional[List[Entity]] = None,
        candidate_merges: Optional[List[CandidateMerge]] = None,
        merge_history: Optional[List[MergeDecision]] = None,
    ):
        self._entities: Dict[str, Entity] = {}
        self._candidate_merges: List[CandidateMerge] = candidate_merges or []
        self._merge_history: List[MergeDecision] = merge_history or []

        if entities:
            for ent in entities:
                self._entities[ent.id] = ent

    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the store."""
        self._entities[entity.id] = entity

    def get_all_entities(self) -> List[Entity]:
        """Return all deduplicated entities."""
        return list(self._entities.values())

    def get_entity_by_id(self, entity_id: str) -> Optional[Entity]:
        """Lookup entity by its unique ID."""
        return self._entities.get(entity_id)

    def get_entities_by_source_fir(self, fir_id: str) -> List[Entity]:
        """Filter entities traceable back to a specific source FIR ID."""
        target_fir = str(fir_id).strip()
        return [
            ent for ent in self._entities.values()
            if target_fir in ent.source_FIR_ids
        ]

    def get_entities_by_type(self, entity_type: Union[EntityType, str]) -> List[Entity]:
        """Filter entities by type (e.g. Person, Phone)."""
        type_val = entity_type.value if isinstance(entity_type, EntityType) else str(entity_type)
        return [
            ent for ent in self._entities.values()
            if ent.type.value == type_val
        ]

    def get_candidate_merges(self) -> List[CandidateMerge]:
        """Return low-confidence pairs flagged for human review."""
        return list(self._candidate_merges)

    def get_merge_history(self) -> List[MergeDecision]:
        """Return full audit log of merge decisions."""
        return list(self._merge_history)

    def to_dict(self) -> Dict[str, Any]:
        """Convert entire store state to a serializable dictionary."""
        return {
            "entities": [ent.model_dump() for ent in self._entities.values()],
            "candidate_merges": [c.model_dump() for c in self._candidate_merges],
            "merge_history": [m.model_dump() for m in self._merge_history],
            "summary": {
                "total_entities": len(self._entities),
                "total_candidate_merges": len(self._candidate_merges),
                "total_merges_performed": len(self._merge_history),
            }
        }

    def export_json(self, filepath: Union[str, Path], indent: int = 2) -> None:
        """Export store state to a JSON file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=indent)

    def export_csv(self, filepath: Union[str, Path]) -> None:
        """Export entity list to a CSV file for tabular inspection."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        rows = []
        for ent in self._entities.values():
            rows.append({
                "id": ent.id,
                "type": ent.type.value,
                "canonical_value": ent.canonical_value,
                "display_value": ent.display_value,
                "source_FIR_ids": ",".join(ent.source_FIR_ids),
                "mentions_count": len(ent.raw_mentions),
                "confidence": ent.confidence,
                "merges_count": len(ent.merge_history),
            })

        df = pd.DataFrame(rows)
        df.to_csv(path, index=False)
