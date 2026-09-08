"""
Pydantic data models for FIR Extraction & Entity Resolution (Phase 1).
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator


class EntityType(str, Enum):
    PERSON = "Person"
    PHONE = "Phone"
    EMAIL = "Email"
    ACCOUNT = "Account"
    ORGANIZATION = "Organization"
    LOCATION = "Location"
    DEVICE = "Device"
    IP = "IP"
    TRANSACTION = "Transaction"
    EVENT = "Event"
    CASE_REF = "CaseRef"


class RawFIR(BaseModel):
    """
    Internal representation of raw structured FIR record.
    Tolerates missing, null, or inconsistent fields gracefully.
    """
    model_config = ConfigDict(extra="allow")

    case_ref: str
    date: Optional[str] = None
    complainant_name: Optional[str] = None
    complainant_address: Optional[str] = None
    accused_name: Optional[Union[str, List[str]]] = None
    accused_address: Optional[str] = None
    narrative_text: Optional[str] = ""
    phone_numbers_mentioned: List[str] = Field(default_factory=list)
    amounts_mentioned: List[str] = Field(default_factory=list)

    @field_validator("case_ref", mode="before")
    @classmethod
    def validate_case_ref(cls, v: Any) -> str:
        if v is None or str(v).strip() == "":
            raise ValueError("case_ref cannot be empty")
        return str(v).strip()

    @field_validator("phone_numbers_mentioned", "amounts_mentioned", mode="before")
    @classmethod
    def validate_list_fields(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            # Split comma separated if string passed
            return [item.strip() for item in v.split(",") if item.strip()]
        if isinstance(v, list):
            return [str(item).strip() for item in v if item is not None and str(item).strip()]
        return []


class RawMention(BaseModel):
    """
    Represents an unprocessed mention extracted from an FIR field or narrative text.
    Maintains complete provenance back to source FIR.
    """
    entity_type: EntityType
    raw_value: str
    source_FIR_id: str
    field_source: str  # e.g., 'complainant_name', 'narrative_text'
    confidence: float = 1.0


class MergeDecision(BaseModel):
    """
    Audit log record explaining why two entity representations were merged.
    Supports full explainability.
    """
    entity_id_1: str
    entity_id_2: str
    merged_entity_id: str
    merge_type: str  # e.g., 'exact_match', 'fuzzy_match', 'shared_identifier'
    confidence: float
    reasoning: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class CandidateMerge(BaseModel):
    """
    Flags ambiguous entity pairs for human review rather than silent auto-merging.
    """
    entity_id_1: str
    entity_id_2: str
    entity_1_value: str
    entity_2_value: str
    entity_type: EntityType
    similarity_score: float
    reasoning: str


class Entity(BaseModel):
    """
    Normalized, deduplicated Entity contract exposed to downstream Phase 2.
    """
    id: str
    type: EntityType
    canonical_value: str
    display_value: str
    source_FIR_ids: List[str]
    raw_mentions: List[RawMention]
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    merge_history: List[MergeDecision] = Field(default_factory=list)
