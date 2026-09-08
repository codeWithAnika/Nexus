from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ResolutionDecision(StrEnum):
    CREATED_NEW = "CREATED_NEW"
    MATCHED_EXISTING_SAME_FIR = "MATCHED_EXISTING_SAME_FIR"
    MATCHED_EXISTING_CROSS_FIR = "MATCHED_EXISTING_CROSS_FIR"
    KEPT_SEPARATE_CROSS_FIR = "KEPT_SEPARATE_CROSS_FIR"
    KEPT_SEPARATE_AMBIGUOUS = "KEPT_SEPARATE_AMBIGUOUS"
    MATCHED_EXISTING = "MATCHED_EXISTING"
    KEPT_SEPARATE = "KEPT_SEPARATE"


@dataclass(frozen=True)
class CandidateResolution:
    temp_id: str
    decision: ResolutionDecision
    reason: str
    entity_type: str
    raw_value: str
    normalized_value: str
    case_id: int
    fir_id: int
    dataset_image_id: int
    source_evidence_id: int
    canonical_entity_id: int | None = None
    canonical_entity_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "temp_id": self.temp_id,
            "decision": self.decision.value,
            "reason": self.reason,
            "entity_type": self.entity_type,
            "raw_value": self.raw_value,
            "normalized_value": self.normalized_value,
            "case_id": self.case_id,
            "fir_id": self.fir_id,
            "dataset_image_id": self.dataset_image_id,
            "source_evidence_id": self.source_evidence_id,
            "canonical_entity_id": self.canonical_entity_id,
            "canonical_entity_name": self.canonical_entity_name,
        }


@dataclass
class PilotResolutionReport:
    pilot_image_ids: tuple[int, ...]
    total_candidates_processed: int
    canonical_entities_total: int = 0
    canonical_entities_created: int = 0
    canonical_entities_reused: int = 0
    provenance_rows_total: int = 0
    provenance_rows_created: int = 0
    provenance_rows_reused: int = 0
    identifiers_created: int = 0
    relationships_count: int = 0
    analyses_count: int = 0
    alerts_count: int = 0
    cross_fir_person_matches_prevented: int = 0
    cross_fir_station_matches: int = 0
    cross_fir_statute_matches: int = 0
    entities_by_type: dict[str, int] = field(default_factory=dict)
    candidates_by_decision: dict[str, int] = field(default_factory=dict)
    resolutions: list[CandidateResolution] = field(default_factory=list)
    rejections: list[dict[str, Any]] = field(default_factory=list)
    is_idempotent_rerun: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "pilot_image_ids": list(self.pilot_image_ids),
            "total_candidates_processed": self.total_candidates_processed,
            "canonical_entities_total": self.canonical_entities_total,
            "canonical_entities_created": self.canonical_entities_created,
            "canonical_entities_reused": self.canonical_entities_reused,
            "provenance_rows_total": self.provenance_rows_total,
            "provenance_rows_created": self.provenance_rows_created,
            "provenance_rows_reused": self.provenance_rows_reused,
            "identifiers_created": self.identifiers_created,
            "relationships_count": self.relationships_count,
            "analyses_count": self.analyses_count,
            "alerts_count": self.alerts_count,
            "cross_fir_person_matches_prevented": self.cross_fir_person_matches_prevented,
            "cross_fir_station_matches": self.cross_fir_station_matches,
            "cross_fir_statute_matches": self.cross_fir_statute_matches,
            "entities_by_type": self.entities_by_type,
            "candidates_by_decision": self.candidates_by_decision,
            "resolutions": [r.to_dict() for r in self.resolutions],
            "rejections": self.rejections,
            "is_idempotent_rerun": self.is_idempotent_rerun,
        }
