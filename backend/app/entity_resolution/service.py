from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.entity_extraction.config import (
    DEFAULT_CONFIG,
    FULL_DATASET_IMAGE_IDS,
    PILOT_IMAGE_IDS,
    VALIDATION_BATCH_IMAGE_IDS,
)
from app.entity_extraction.extractor import extract_batch_entities, extract_pilot_entities
from app.entity_resolution.models import (
    CandidateResolution,
    PilotResolutionReport,
    ResolutionDecision,
)
from app.entity_resolution.resolver import ConservativeEntityResolver
from app.models.alert import Alert
from app.models.analysis import Analysis
from app.models.entity import Entity, EntityMentionProvenance, EntityType
from app.models.entity_identifier import EntityIdentifier
from app.models.evidence import Evidence
from app.models.fir import FIR
from app.models.relationship import Relationship


class CaseOwnershipMismatchError(ValueError):
    pass


class PilotScopeError(ValueError):
    pass


def resolve_and_persist_pilot(
    *,
    db: Session,
    handoff: dict[str, Any] | None = None,
    requested_image_ids: set[int] | None = None,
    extractor_version: str | None = None,
    allowed_scope: frozenset[int] = PILOT_IMAGE_IDS,
) -> PilotResolutionReport:
    """Resolve and persist extraction candidates transactionally.

    Guarantees:
    - Atomicity: All entities & provenances are committed together; on error, rolled back.
    - Idempotency: Running twice will reuse existing entities and provenances without duplicates.
    - Ownership verification: candidate.case_id == evidence.case_id and fir_id consistency.
    - Zero relationships, zero analyses, zero alerts.
    - Zero fake EntityIdentifiers.
    - Conservative Cross-FIR Person Policy: Keeps persons from different FIRs separate.
    """
    target_ids = requested_image_ids if requested_image_ids is not None else set(allowed_scope)
    invalid_ids = target_ids - allowed_scope
    if invalid_ids:
        raise PilotScopeError(
            f"Safety guard: requested image IDs {sorted(invalid_ids)} are outside approved scope {sorted(allowed_scope)}"
        )

    if handoff is None:
        handoff, _ = extract_batch_entities(db=db, requested_image_ids=target_ids, allowed_scope=allowed_scope)

    version = extractor_version or handoff.get("metadata", {}).get("extractor_version", DEFAULT_CONFIG.extractor_version)
    candidates: list[dict[str, Any]] = handoff.get("entities", [])

    # Filter candidates to target image IDs if needed
    pilot_candidates = [c for c in candidates if c.get("dataset_image_id") in target_ids]
    sorted_image_ids = tuple(sorted(target_ids))

    report = PilotResolutionReport(
        pilot_image_ids=sorted_image_ids,
        total_candidates_processed=len(pilot_candidates),
    )

    if not pilot_candidates:
        return report

    # 1. Ownership & Linkage Pre-Validation
    for cand in pilot_candidates:
        ev_id = cand["source_evidence_id"]
        evidence = db.get(Evidence, ev_id)
        if evidence is None:
            raise CaseOwnershipMismatchError(f"Evidence {ev_id} not found for candidate {cand['temp_id']}")
        if evidence.case_id != cand["case_id"]:
            raise CaseOwnershipMismatchError(
                f"Case ownership mismatch for candidate {cand['temp_id']}: candidate case_id={cand['case_id']} != evidence case_id={evidence.case_id}"
            )
        if cand.get("fir_id") and evidence.fir_id != cand["fir_id"]:
            raise CaseOwnershipMismatchError(
                f"FIR linkage mismatch for candidate {cand['temp_id']}: candidate fir_id={cand['fir_id']} != evidence fir_id={evidence.fir_id}"
            )

    # 2. Pre-load existing entities and provenances for idempotency
    case_ids = {c["case_id"] for c in pilot_candidates}
    evidence_ids = {c["source_evidence_id"] for c in pilot_candidates}

    existing_entities = db.scalars(
        select(Entity).where(Entity.case_id.in_(case_ids))
    ).all()

    resolver = ConservativeEntityResolver()
    # Map entity id -> Entity
    entity_cache: dict[int, Entity] = {e.id: e for e in existing_entities}

    existing_provenances = db.scalars(
        select(EntityMentionProvenance).where(EntityMentionProvenance.evidence_id.in_(evidence_ids))
    ).all()
    # Map (evidence_id, source_index, start_char, end_char) -> EntityMentionProvenance
    existing_prov_map: dict[tuple[int, int | None, int | None, int | None], EntityMentionProvenance] = {
        (p.evidence_id, p.source_index, p.start_char, p.end_char): p for p in existing_provenances
    }

    # Register pre-existing entities with resolver
    for ent in existing_entities:
        # Find fir_id if any provenance exists for this entity
        fir_id = None
        for p in existing_provenances:
            if p.entity_id == ent.id:
                ev = db.get(Evidence, p.evidence_id)
                if ev and ev.fir_id:
                    fir_id = ev.fir_id
                    break
        resolver.register_existing_canonical_entity(
            entity_id=ent.id,
            case_id=ent.case_id,
            entity_type=ent.entity_type.value,
            name=ent.name,
            normalized_name=ent.normalized_name or ent.name,
            fir_id=fir_id,
        )

    # 3. Transactional Resolution and Persistence
    created_entities: list[Entity] = []
    created_provenances: list[EntityMentionProvenance] = []
    reused_entity_ids: set[int] = set()
    reused_prov_ids: set[int] = set()

    try:
        for cand in pilot_candidates:
            res = resolver.resolve_candidate(cand)
            canonical_entity: Entity | None = None

            # Check if this exact mention provenance was ALREADY persisted (idempotent rerun)
            prov_data = cand["provenance"]
            span_data = prov_data["span"]
            source_index = prov_data.get("source_index")
            start_char = span_data.get("start_char")
            end_char = span_data.get("end_char")
            prov_key = (cand["source_evidence_id"], source_index, start_char, end_char)

            if prov_key in existing_prov_map:
                existing_prov = existing_prov_map[prov_key]
                reused_prov_ids.add(existing_prov.id)
                canonical_entity = entity_cache.get(existing_prov.entity_id) or db.get(Entity, existing_prov.entity_id)
                if canonical_entity:
                    reused_entity_ids.add(canonical_entity.id)

            if canonical_entity is None:
                # Needs new Entity or existing Entity lookup
                if res.decision in {ResolutionDecision.CREATED_NEW, ResolutionDecision.KEPT_SEPARATE_CROSS_FIR}:
                    canonical_entity = Entity(
                        case_id=cand["case_id"],
                        entity_type=EntityType(cand["extraction_entity_type"]),
                        name=cand["raw_value"],
                        normalized_name=cand["normalized_value"],
                        confidence=cand.get("entity_confidence"),
                    )
                    db.add(canonical_entity)
                    db.flush()  # assign canonical_entity.id without committing
                    created_entities.append(canonical_entity)
                    entity_cache[canonical_entity.id] = canonical_entity
                    resolver.update_canonical_entity_id(
                        cand["case_id"],
                        cand["extraction_entity_type"],
                        cand["normalized_value"],
                        canonical_entity.id,
                        fir_id=cand["fir_id"],
                    )
                else:
                    # MATCHED_EXISTING_SAME_FIR or MATCHED_EXISTING_CROSS_FIR
                    target_id = res.canonical_entity_id
                    if target_id is not None:
                        canonical_entity = entity_cache.get(target_id) or db.get(Entity, target_id)
                        if canonical_entity:
                            reused_entity_ids.add(canonical_entity.id)

            if canonical_entity is None:
                raise RuntimeError(f"Failed to obtain canonical entity for candidate {cand['temp_id']}")

            # Update resolution record with assigned canonical ID
            final_res = CandidateResolution(
                temp_id=res.temp_id,
                decision=res.decision,
                reason=res.reason,
                entity_type=res.entity_type,
                raw_value=res.raw_value,
                normalized_value=res.normalized_value,
                case_id=res.case_id,
                fir_id=res.fir_id,
                dataset_image_id=res.dataset_image_id,
                source_evidence_id=res.source_evidence_id,
                canonical_entity_id=canonical_entity.id,
                canonical_entity_name=canonical_entity.name,
            )
            report.resolutions.append(final_res)
            report.candidates_by_decision[res.decision.value] = (
                report.candidates_by_decision.get(res.decision.value, 0) + 1
            )

            # Cross-FIR tracking metrics
            if res.decision == ResolutionDecision.KEPT_SEPARATE_CROSS_FIR:
                report.cross_fir_person_matches_prevented += 1
            elif res.decision == ResolutionDecision.MATCHED_EXISTING_CROSS_FIR:
                if cand["extraction_entity_type"] == "POLICE_STATION":
                    report.cross_fir_station_matches += 1
                elif cand["extraction_entity_type"] == "STATUTE":
                    report.cross_fir_statute_matches += 1

            # Step C: EntityIdentifier
            # Only create when extraction candidate explicitly contains a legitimate business identifier
            for ident_data in cand.get("identifiers", []):
                ident_type = ident_data.get("identifier_type")
                if ident_type in {"PHONE", "EMAIL", "BANK_ACCOUNT", "VEHICLE_REGISTRATION"}:
                    ident = EntityIdentifier(
                        entity_id=canonical_entity.id,
                        identifier_type=ident_type,
                        identifier_value=ident_data["identifier_value"],
                        normalized_value=ident_data.get("normalized_value"),
                        confidence=ident_data.get("confidence"),
                        source_evidence_id=cand["source_evidence_id"],
                    )
                    db.add(ident)
                    report.identifiers_created += 1

            # Step D: EntityMentionProvenance (if not already existing)
            if prov_key not in existing_prov_map:
                bbox = prov_data.get("bbox", [None, None, None, None])
                emp = EntityMentionProvenance(
                    entity_id=canonical_entity.id,
                    evidence_id=cand["source_evidence_id"],
                    matched_text=span_data.get("matched_text", cand["raw_value"]),
                    start_char=start_char,
                    end_char=end_char,
                    ocr_confidence=cand.get("ocr_confidence"),
                    extraction_confidence=cand.get("extraction_confidence", 1.0),
                    final_confidence=cand.get("entity_confidence", 1.0),
                    low_ocr_confidence=cand.get("low_ocr_confidence", False),
                    extraction_method=cand.get("extraction_method", "rule_based"),
                    extractor_version=version,
                    source_index=source_index,
                    reconstructed_order=prov_data.get("reconstructed_order"),
                    category_id=prov_data.get("category_id"),
                    bbox_x1=float(bbox[0]) if bbox[0] is not None else None,
                    bbox_y1=float(bbox[1]) if bbox[1] is not None else None,
                    bbox_x2=float(bbox[2]) if bbox[2] is not None else None,
                    bbox_y2=float(bbox[3]) if bbox[3] is not None else None,
                    original_text=prov_data.get("original_text"),
                )
                db.add(emp)
                created_provenances.append(emp)
                existing_prov_map[prov_key] = emp

        db.commit()
    except Exception:
        db.rollback()
        raise

    # 4. Compile final report counts
    report.canonical_entities_created = len(created_entities)
    report.canonical_entities_reused = len(reused_entity_ids)
    all_entity_ids = {e.id for e in created_entities} | reused_entity_ids
    report.canonical_entities_total = len(all_entity_ids)

    report.provenance_rows_created = len(created_provenances)
    report.provenance_rows_reused = len(reused_prov_ids)
    report.provenance_rows_total = report.provenance_rows_created + report.provenance_rows_reused

    report.is_idempotent_rerun = (report.canonical_entities_created == 0 and report.canonical_entities_reused > 0)

    # Entity counts by type
    if all_entity_ids:
        type_counts = db.execute(
            select(Entity.entity_type, func.count(Entity.id))
            .where(Entity.id.in_(all_entity_ids))
            .group_by(Entity.entity_type)
        ).all()
        report.entities_by_type = {t.value: cnt for t, cnt in type_counts}

    # ER creates zero relationships, analyses, alerts
    report.relationships_count = 0
    report.analyses_count = 0
    report.alerts_count = 0

    return report


def resolve_and_persist_validation_batch(
    *,
    db: Session,
    handoff: dict[str, Any] | None = None,
    requested_image_ids: set[int] | None = None,
    extractor_version: str | None = None,
) -> PilotResolutionReport:
    """Convenience helper to resolve and persist the 25-FIR validation batch (Image IDs 0-24)."""
    target_ids = requested_image_ids if requested_image_ids is not None else set(VALIDATION_BATCH_IMAGE_IDS)
    return resolve_and_persist_pilot(
        db=db,
        handoff=handoff,
        requested_image_ids=target_ids,
        extractor_version=extractor_version,
        allowed_scope=VALIDATION_BATCH_IMAGE_IDS,
    )


def resolve_and_persist_full_dataset(
    *,
    db: Session,
    handoff: dict[str, Any] | None = None,
    requested_image_ids: set[int] | None = None,
    extractor_version: str | None = None,
) -> PilotResolutionReport:
    """Convenience helper to resolve and persist the full dataset (544 usable image records)."""
    target_ids = requested_image_ids if requested_image_ids is not None else set(FULL_DATASET_IMAGE_IDS)
    return resolve_and_persist_pilot(
        db=db,
        handoff=handoff,
        requested_image_ids=target_ids,
        extractor_version=extractor_version,
        allowed_scope=FULL_DATASET_IMAGE_IDS,
    )
