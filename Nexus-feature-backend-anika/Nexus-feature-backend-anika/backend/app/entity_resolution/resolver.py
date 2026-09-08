from __future__ import annotations

from typing import Any

from app.entity_resolution.models import (
    CandidateResolution,
    ResolutionDecision,
)
from app.models.entity import EntityType


class ConservativeEntityResolver:
    """Conservative, deterministic Entity Resolution engine for controlled validation batches.

    Guarantees:
    - Type Isolation: Never merges across different EntityTypes (e.g. PERSON with POLICE_STATION).
    - Scope Isolation: Never merges across different Cases.
    - Zero Graph Inferences: Never creates relationships from co-occurrence.
    - Conservative Person Policy:
      - Within same FIR: Deterministic exact normalized match -> MATCHED_EXISTING_SAME_FIR.
      - Across different FIRs: Identical normalized name without corroborating identifiers
        is KEPT_SEPARATE_CROSS_FIR to prevent false identity merges (homonym collisions).
    - Institutional & Statutory Canonicalization:
      - POLICE_STATION and STATUTE canonicalize case-wide (MATCHED_EXISTING_SAME_FIR / MATCHED_EXISTING_CROSS_FIR).
    - Ambiguous or short values (< 2 chars) are KEPT_SEPARATE_AMBIGUOUS.
    - Explicit rationale recorded for every candidate decision.
    """

    def __init__(self, *, cross_fir_person_merge: bool = False) -> None:
        self.cross_fir_person_merge = cross_fir_person_merge
        # Key: (case_id, entity_type, normalized_value) -> registry entry dict
        self._canonical_registry: dict[tuple[int, str, str], dict[str, Any]] = {}
        self._decisions: list[CandidateResolution] = []

    def register_existing_canonical_entity(
        self,
        *,
        entity_id: int,
        case_id: int,
        entity_type: str,
        name: str,
        normalized_name: str,
        fir_id: int | None = None,
    ) -> None:
        """Register a pre-existing canonical Entity (for idempotency during reruns)."""
        key = (case_id, entity_type, normalized_name.strip().lower())
        if key not in self._canonical_registry:
            self._canonical_registry[key] = {
                "entity_id": entity_id,
                "name": name,
                "normalized_name": normalized_name,
                "entity_type": entity_type,
                "case_id": case_id,
                "first_fir_id": fir_id,
                "fir_entities": {fir_id: {"entity_id": entity_id, "name": name}} if fir_id is not None else {},
            }
        else:
            if fir_id is not None:
                self._canonical_registry[key].setdefault("fir_entities", {})[fir_id] = {
                    "entity_id": entity_id,
                    "name": name,
                }

    def resolve_candidate(
        self,
        candidate: dict[str, Any],
        *,
        persisted_entity_id: int | None = None,
    ) -> CandidateResolution:
        """Resolve a single extraction candidate to a canonical entity."""
        temp_id = candidate["temp_id"]
        case_id = candidate["case_id"]
        fir_id = candidate["fir_id"]
        dataset_image_id = candidate["dataset_image_id"]
        source_evidence_id = candidate["source_evidence_id"]
        raw_type = candidate["extraction_entity_type"]
        raw_value = candidate["raw_value"].strip()
        normalized_value = candidate["normalized_value"].strip()

        # Validate entity type is a supported canonical EntityType
        try:
            canonical_type = EntityType(raw_type).value
        except ValueError:
            resolution = CandidateResolution(
                temp_id=temp_id,
                decision=ResolutionDecision.KEPT_SEPARATE_AMBIGUOUS,
                reason=f"Unsupported entity type '{raw_type}' - kept separate without canonical merge",
                entity_type=raw_type,
                raw_value=raw_value,
                normalized_value=normalized_value,
                case_id=case_id,
                fir_id=fir_id,
                dataset_image_id=dataset_image_id,
                source_evidence_id=source_evidence_id,
            )
            self._decisions.append(resolution)
            return resolution

        # Ambiguity check: empty or trivial normalized value cannot match
        if not normalized_value or len(normalized_value) < 2:
            resolution = CandidateResolution(
                temp_id=temp_id,
                decision=ResolutionDecision.KEPT_SEPARATE_AMBIGUOUS,
                reason="Normalized value is empty or too short - kept separate as ambiguous",
                entity_type=canonical_type,
                raw_value=raw_value,
                normalized_value=normalized_value,
                case_id=case_id,
                fir_id=fir_id,
                dataset_image_id=dataset_image_id,
                source_evidence_id=source_evidence_id,
            )
            self._decisions.append(resolution)
            return resolution

        key = (case_id, canonical_type, normalized_value.lower())

        if key in self._canonical_registry:
            target = self._canonical_registry[key]

            if canonical_type == "PERSON" and not self.cross_fir_person_merge:
                fir_entities = target.setdefault("fir_entities", {})
                initial_fir = target.get("first_fir_id")

                if initial_fir is not None and fir_id != initial_fir:
                    # Different FIR from the initial FIR -> KEPT_SEPARATE_CROSS_FIR
                    existing_fir_target = fir_entities.get(fir_id)
                    ent_id = existing_fir_target.get("entity_id") if existing_fir_target else persisted_entity_id
                    ent_name = existing_fir_target.get("name") if existing_fir_target else raw_value
                    if fir_id not in fir_entities:
                        fir_entities[fir_id] = {"entity_id": persisted_entity_id, "name": raw_value}

                    resolution = CandidateResolution(
                        temp_id=temp_id,
                        decision=ResolutionDecision.KEPT_SEPARATE_CROSS_FIR,
                        reason=(
                            f"Conservative validation-batch policy: same normalized person name '{normalized_value}' "
                            f"in different FIR (fir_id={fir_id} != initial fir_id={initial_fir}) kept separate to prevent false identity merges"
                        ),
                        entity_type=canonical_type,
                        raw_value=raw_value,
                        normalized_value=normalized_value,
                        case_id=case_id,
                        fir_id=fir_id,
                        dataset_image_id=dataset_image_id,
                        source_evidence_id=source_evidence_id,
                        canonical_entity_id=ent_id,
                        canonical_entity_name=ent_name,
                    )
                else:
                    # Same FIR as initial FIR: match existing
                    same_fir_target = fir_entities.get(fir_id, target)
                    resolution = CandidateResolution(
                        temp_id=temp_id,
                        decision=ResolutionDecision.MATCHED_EXISTING_SAME_FIR,
                        reason=f"Deterministic exact match on normalized person name '{normalized_value}' within the same FIR (fir_id={fir_id})",
                        entity_type=canonical_type,
                        raw_value=raw_value,
                        normalized_value=normalized_value,
                        case_id=case_id,
                        fir_id=fir_id,
                        dataset_image_id=dataset_image_id,
                        source_evidence_id=source_evidence_id,
                        canonical_entity_id=same_fir_target.get("entity_id"),
                        canonical_entity_name=same_fir_target.get("name"),
                    )
            else:
                # POLICE_STATION or STATUTE (or PERSON if cross_fir_person_merge=True)
                initial_fir = target.get("first_fir_id")
                is_same_fir = (initial_fir == fir_id)
                decision = (
                    ResolutionDecision.MATCHED_EXISTING_SAME_FIR
                    if is_same_fir
                    else ResolutionDecision.MATCHED_EXISTING_CROSS_FIR
                )
                scope_desc = f"within same FIR {fir_id}" if is_same_fir else f"across FIRs (current fir_id={fir_id}, initial fir_id={initial_fir})"
                resolution = CandidateResolution(
                    temp_id=temp_id,
                    decision=decision,
                    reason=f"Deterministic {canonical_type} match on case_id={case_id}, normalized_name='{normalized_value}' {scope_desc}",
                    entity_type=canonical_type,
                    raw_value=raw_value,
                    normalized_value=normalized_value,
                    case_id=case_id,
                    fir_id=fir_id,
                    dataset_image_id=dataset_image_id,
                    source_evidence_id=source_evidence_id,
                    canonical_entity_id=target.get("entity_id"),
                    canonical_entity_name=target.get("name"),
                )
        else:
            # First occurrence -> Created New canonical entity
            self._canonical_registry[key] = {
                "entity_id": persisted_entity_id,
                "name": raw_value,
                "normalized_name": normalized_value,
                "entity_type": canonical_type,
                "case_id": case_id,
                "first_fir_id": fir_id,
                "fir_entities": {fir_id: {"entity_id": persisted_entity_id, "name": raw_value}},
            }
            resolution = CandidateResolution(
                temp_id=temp_id,
                decision=ResolutionDecision.CREATED_NEW,
                reason=f"First occurrence of entity_type={canonical_type} with normalized_name='{normalized_value}' in case {case_id} (fir_id={fir_id})",
                entity_type=canonical_type,
                raw_value=raw_value,
                normalized_value=normalized_value,
                case_id=case_id,
                fir_id=fir_id,
                dataset_image_id=dataset_image_id,
                source_evidence_id=source_evidence_id,
                canonical_entity_id=persisted_entity_id,
                canonical_entity_name=raw_value,
            )

        self._decisions.append(resolution)
        return resolution

    def update_canonical_entity_id(
        self,
        case_id: int,
        entity_type: str,
        normalized_value: str,
        entity_id: int,
        fir_id: int | None = None,
    ) -> None:
        key = (case_id, entity_type, normalized_value.strip().lower())
        if key in self._canonical_registry:
            reg = self._canonical_registry[key]
            if reg.get("entity_id") is None:
                reg["entity_id"] = entity_id
            if fir_id is not None and "fir_entities" in reg and fir_id in reg["fir_entities"]:
                reg["fir_entities"][fir_id]["entity_id"] = entity_id

    @property
    def decisions(self) -> list[CandidateResolution]:
        return list(self._decisions)
