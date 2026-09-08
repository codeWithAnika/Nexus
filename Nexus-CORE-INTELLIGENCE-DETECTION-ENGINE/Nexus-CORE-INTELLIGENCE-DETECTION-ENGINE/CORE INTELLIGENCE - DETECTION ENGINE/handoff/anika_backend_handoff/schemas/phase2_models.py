"""
Pydantic data models for Relationship Mining & Graph Construction (Phase 2).
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RelationType(str, Enum):
    OWNS = "owns"
    USES = "uses"
    VISITED = "visited"
    TRANSACTION = "transaction"
    CONNECTED_TO = "connected_to"
    ASSOCIATED_WITH = "associated_with"


class SourceType(str, Enum):
    STRUCTURED_FIELD = "structured_field"
    CO_OCCURRENCE = "co_occurrence"
    LLM_INFERRED = "llm_inferred"


class EdgeWeight(BaseModel):
    """
    Transparent edge weight representation.
    Preserves weight components separately for explainability in downstream Phase 3/4.
    """
    base_weight: float
    fir_support_count: int
    source_types: List[str] = Field(default_factory=list)
    entity_confidence_product: float = 1.0
    computed_weight: float

    @classmethod
    def calculate(
        cls,
        base_weight: float,
        fir_ids: List[str],
        source_types: List[str],
        conf1: float = 1.0,
        conf2: float = 1.0,
    ) -> "EdgeWeight":
        support_count = max(1, len(set(fir_ids)))
        conf_product = round(conf1 * conf2, 3)
        # Weight formula: (base_weight + 0.25 * (support_count - 1)) * conf_product
        computed = round((base_weight + 0.25 * (support_count - 1)) * conf_product, 3)
        return cls(
            base_weight=base_weight,
            fir_support_count=support_count,
            source_types=list(set(source_types)),
            entity_confidence_product=conf_product,
            computed_weight=computed,
        )


class Relationship(BaseModel):
    """
    Typed, directed relationship model linking two resolved entities.
    Tracks provenance back to source FIRs and extraction method.
    """
    id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: RelationType
    source_type: str  # 'structured_field' | 'co_occurrence' | 'llm_inferred'
    source_FIR_ids: List[str]
    evidence: str  # field name or narrative snippet
    weight: EdgeWeight
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
