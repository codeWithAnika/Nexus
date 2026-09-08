"""
Intelligence Integration Service
Bridges Backend canonical entities and provenances into Aayushman's Phase 2, 3, and 4
intelligence pipeline, then transactionally persists Relationships, Analyses, and Alerts
into Oracle XE.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.models.analysis import Analysis, RiskLevel
from app.models.case import Case
from app.models.entity import Entity, EntityMentionProvenance, EntityType
from app.models.evidence import Evidence
from app.models.fir import FIR
from app.models.relationship import Relationship, RelationshipType

logger = logging.getLogger(__name__)

# Dynamically ensure Aayushman's fir_intelligence package is discoverable on sys.path
def _ensure_fir_intelligence_path() -> None:
    repo_aym = Path(__file__).resolve().parent.parent.parent.parent / "aayushman work"
    aym_work = repo_aym / "SIH PS189" / "Aayuushman's work"
    
    # Auto-extract zip if directory does not exist but zip does
    if not aym_work.exists() and (repo_aym / "SIH PS189.zip").exists():
        import zipfile
        try:
            with zipfile.ZipFile(repo_aym / "SIH PS189.zip", "r") as z:
                z.extractall(repo_aym)
        except Exception:
            pass

    candidate_paths = [
        aym_work,
        Path(__file__).resolve().parent.parent.parent / "aayushman" / "SIH PS189" / "Aayuushman's work",
        Path(r"C:\Users\anika\.gemini\antigravity\brain\318c5340-7670-4f40-936e-0cc42bdfda50\scratch\aayushman\SIH PS189\Aayuushman's work"),
    ]
    for p in candidate_paths:
        if p.exists() and (p / "fir_intelligence").exists():
            p_str = str(p)
            if p_str not in sys.path:
                sys.path.insert(0, p_str)
            return

_ensure_fir_intelligence_path()

try:
    from fir_intelligence.phase1_extraction import models as aay_p1
    from fir_intelligence.phase1_extraction.entity_store import EntityStore
    from fir_intelligence.phase2_graph import models as aay_p2
    from fir_intelligence.phase2_graph.graph_builder import GraphBuilder
    from fir_intelligence.phase2_graph.relationship_rules import (
        extract_cooccurrence_relationships,
        extract_structured_field_relationships,
    )
    from fir_intelligence.phase3_analytics import models as aay_p3
    from fir_intelligence.phase3_analytics.analyzer import GraphAnalyzer
    from fir_intelligence.phase4_scoring import models as aay_p4
    from fir_intelligence.phase4_scoring.alert_generator import AlertGenerator
    from fir_intelligence.phase4_scoring.scoring import RiskScorer
except ImportError as err:
    logger.warning("Aayushman fir_intelligence package could not be imported: %s", err)
    aay_p1 = None
    aay_p2 = None
    aay_p3 = None
    aay_p4 = None


class IntelligenceIntegrationError(Exception):
    """Base exception for intelligence integration service."""
    pass


class CaseNotFoundError(IntelligenceIntegrationError):
    """Raised when specified case does not exist."""
    pass


class InvalidEntityReferenceError(IntelligenceIntegrationError):
    """Raised when an edge references an entity unknown to Oracle DB."""
    pass


@dataclass
class IdMapper:
    """Bi-directional mapping between Oracle integer entity IDs and Aayushman string IDs."""
    db_to_aayushman: Dict[int, str] = field(default_factory=dict)
    aayushman_to_db: Dict[str, int] = field(default_factory=dict)

    def register(self, db_id: int, aay_id: str) -> None:
        self.db_to_aayushman[db_id] = aay_id
        self.aayushman_to_db[aay_id] = db_id

    def get_db_id(self, aay_id: str) -> Optional[int]:
        return self.aayushman_to_db.get(aay_id)

    def get_aayushman_id(self, db_id: int) -> Optional[str]:
        return self.db_to_aayushman.get(db_id)


def resolve_external_fir_reference(ref: str, db: Session) -> Optional[int]:
    """
    Deterministically maps an external FIR reference string (e.g. 'FIR-575', '575', 'ICDAR-0')
    to the Oracle fir.id.
    """
    if not ref:
        return None
    ref_str = str(ref).strip()

    # 1. Check if ref matches directly as an integer ID
    if ref_str.isdigit():
        val = int(ref_str)
        fir = db.scalar(select(FIR).where(FIR.id == val))
        if fir:
            return fir.id
        # Also check dataset_image_id == val
        fir_img = db.scalar(select(FIR).where(FIR.dataset_image_id == val))
        if fir_img:
            return fir_img.id

    # 2. Check 'FIR-<id>' pattern
    if ref_str.upper().startswith("FIR-"):
        suffix = ref_str[4:].strip()
        if suffix.isdigit():
            val = int(suffix)
            fir = db.scalar(select(FIR).where(FIR.id == val))
            if fir:
                return fir.id
            fir_img = db.scalar(select(FIR).where(FIR.dataset_image_id == val))
            if fir_img:
                return fir_img.id

    # 3. Check fir_number exact match
    fir_num = db.scalar(select(FIR).where(FIR.fir_number == ref_str))
    if fir_num:
        return fir_num.id

    # 4. Check if ref is like 'ICDAR-<image_id>'
    if ref_str.upper().startswith("ICDAR-"):
        suffix = ref_str[6:].strip()
        if suffix.isdigit():
            val = int(suffix)
            fir_img = db.scalar(select(FIR).where(FIR.dataset_image_id == val))
            if fir_img:
                return fir_img.id

    return None


def map_entity_type_to_aayushman(ent_type: EntityType) -> aay_p1.EntityType:
    """
    Conservative taxonomy mapping from Oracle EntityType to Aayushman EntityType.
    - PERSON -> Person
    - LOCATION -> Location
    - POLICE_STATION -> Location (for topological linkage if needed)
    - STATUTE -> CaseRef (conservative legal citation; does not fabricate Person or Location)
    - Others -> conservative fallback
    """
    if ent_type == EntityType.PERSON:
        return aay_p1.EntityType.PERSON
    elif ent_type == EntityType.LOCATION:
        return aay_p1.EntityType.LOCATION
    elif ent_type == EntityType.POLICE_STATION:
        return aay_p1.EntityType.LOCATION
    elif ent_type == EntityType.STATUTE:
        return aay_p1.EntityType.CASE_REF
    elif ent_type == EntityType.ORGANIZATION:
        return aay_p1.EntityType.ORGANIZATION
    elif ent_type == EntityType.PHONE:
        return aay_p1.EntityType.PHONE
    elif ent_type == EntityType.EMAIL:
        return aay_p1.EntityType.EMAIL
    elif ent_type == EntityType.TRANSACTION:
        return aay_p1.EntityType.TRANSACTION
    elif ent_type == EntityType.BANK_ACCOUNT:
        return aay_p1.EntityType.ACCOUNT
    else:
        return aay_p1.EntityType.CASE_REF


def map_relationship_type_to_oracle(aay_rel: aay_p2.RelationType) -> RelationshipType:
    """Maps Aayushman RelationType enum to Oracle RelationshipType enum."""
    val = aay_rel.value if hasattr(aay_rel, "value") else str(aay_rel)
    mapping = {
        "owns": RelationshipType.OWNS,
        "uses": RelationshipType.COMMUNICATED_WITH,
        "visited": RelationshipType.LOCATED_AT,
        "transaction": RelationshipType.TRANSFERRED_TO,
        "connected_to": RelationshipType.ASSOCIATED_WITH,
        "associated_with": RelationshipType.ASSOCIATED_WITH,
    }
    return mapping.get(val.lower(), RelationshipType.ASSOCIATED_WITH)


def map_risk_tier_to_oracle(tier: str) -> RiskLevel:
    """Maps risk tier string (LOW, MEDIUM, HIGH) to Oracle RiskLevel enum."""
    t = str(tier).upper().strip()
    if t == "HIGH":
        return RiskLevel.HIGH
    elif t == "MEDIUM":
        return RiskLevel.MEDIUM
    elif t == "CRITICAL":
        return RiskLevel.CRITICAL
    return RiskLevel.LOW


def map_alert_severity_to_oracle(tier: str) -> AlertSeverity:
    """Maps alert risk tier to Oracle AlertSeverity enum."""
    t = str(tier).upper().strip()
    if t == "HIGH":
        return AlertSeverity.HIGH
    elif t == "CRITICAL":
        return AlertSeverity.CRITICAL
    elif t == "MEDIUM":
        return AlertSeverity.MEDIUM
    return AlertSeverity.LOW


class IntelligenceIntegrationService:
    """
    Executes end-to-end graph intelligence over a given case or set of image IDs.
    Transactional, idempotent, deterministic, and preserves complete provenance.
    """

    def __init__(self, db: Session):
        self.db = db

    def run_intelligence_pipeline(
        self,
        case_id: int,
        requested_image_ids: Optional[Set[int]] = None,
    ) -> Dict[str, Any]:
        """
        Executes Phase 2 -> Phase 3 -> Phase 4 and persists results to Oracle.
        """
        if aay_p1 is None:
            raise IntelligenceIntegrationError("Aayushman intelligence modules are not loaded.")

        # 1. Validate Case exists
        case = self.db.scalar(select(Case).where(Case.id == case_id))
        if not case:
            raise CaseNotFoundError(f"Case with id {case_id} not found.")

        # 2. Load canonical entities and their mention provenances
        entities_query = select(Entity).where(Entity.case_id == case_id)
        all_case_entities = list(self.db.scalars(entities_query).all())

        # If requested_image_ids is specified, filter entities linked to those FIRs
        if requested_image_ids is not None:
            # Query evidence matching these FIR image IDs
            firs_query = select(FIR.id).where(
                FIR.case_id == case_id,
                FIR.dataset_image_id.in_(requested_image_ids),
            )
            target_fir_ids = set(self.db.scalars(firs_query).all())

            # Find evidence IDs
            ev_query = select(Evidence.id).where(Evidence.fir_id.in_(target_fir_ids))
            target_ev_ids = set(self.db.scalars(ev_query).all())

            # Find entities with provenance in target evidence
            prov_query = select(EntityMentionProvenance.entity_id).where(
                EntityMentionProvenance.evidence_id.in_(target_ev_ids)
            )
            target_entity_ids = set(self.db.scalars(prov_query).all())
            active_entities = [e for e in all_case_entities if e.id in target_entity_ids]
        else:
            active_entities = all_case_entities

        id_mapper = IdMapper()
        aay_entities: List[aay_p1.Entity] = []

        # Map each Oracle entity to an Aayushman Entity object
        for ent in active_entities:
            aay_id = f"ENT-{ent.id}"
            id_mapper.register(ent.id, aay_id)

            # Gather source FIR references from mention provenances
            provs = ent.mention_provenances
            source_fir_refs: Set[str] = set()
            raw_mentions: List[aay_p1.RawMention] = []

            for p in provs:
                ev = p.evidence
                if ev and ev.fir:
                    # Provide FIR reference string
                    fir_ref = f"FIR-{ev.fir.id}"
                    source_fir_refs.add(fir_ref)
                    raw_mentions.append(
                        aay_p1.RawMention(
                            entity_type=map_entity_type_to_aayushman(ent.entity_type),
                            raw_value=p.matched_text,
                            source_FIR_id=fir_ref,
                            field_source=f"category_{p.category_id}" if p.category_id is not None else "provenance",
                            confidence=p.final_confidence or 1.0,
                        )
                    )

            if not source_fir_refs:
                source_fir_refs.add(f"CASE-{case_id}")

            aay_ent = aay_p1.Entity(
                id=aay_id,
                type=map_entity_type_to_aayushman(ent.entity_type),
                canonical_value=ent.normalized_name or ent.name,
                display_value=ent.name,
                source_FIR_ids=sorted(list(source_fir_refs)),
                raw_mentions=raw_mentions,
                confidence=ent.confidence or 1.0,
                metadata={"oracle_entity_id": ent.id, "oracle_entity_type": ent.entity_type.value},
            )
            aay_entities.append(aay_ent)

        entity_store = EntityStore(entities=aay_entities)

        # 3. Phase 2: Relationship Mining (Deterministic rules only, no LLM required)
        structured_rels = extract_structured_field_relationships(entity_store)
        cooccurrence_rels = extract_cooccurrence_relationships(entity_store)
        raw_relationships = structured_rels + cooccurrence_rels

        # 4. Phase 2: Graph Construction
        builder = GraphBuilder()
        graph = builder.build_from_entity_store(entity_store, raw_relationships)

        # 5. Phase 3: Graph Analytics (Centrality, Louvain Communities, Pattern Detection)
        analyzer = GraphAnalyzer()
        analysis_result = analyzer.run_full_analysis(graph)

        # 6. Phase 4: Risk Scoring & Alerts
        alert_gen = AlertGenerator()
        alerts_payload = alert_gen.generate_alerts(
            analysis_result,
            entity_store=entity_store,
            use_llm=False,
        )

        # 7. Transactional Persistence into Oracle
        try:
            # 7a. Persist Relationships
            created_relationships_count = 0
            for rel in raw_relationships:
                # Map source and target IDs
                src_db_id = id_mapper.get_db_id(rel.source_entity_id)
                tgt_db_id = id_mapper.get_db_id(rel.target_entity_id)

                if src_db_id is None or tgt_db_id is None:
                    raise InvalidEntityReferenceError(
                        f"Relationship references unknown entity ID: {rel.source_entity_id} -> {rel.target_entity_id}"
                    )

                # Resolve primary source FIR ID
                primary_fir_id = None
                evidence_id = None
                if rel.source_FIR_ids:
                    primary_fir_id = resolve_external_fir_reference(rel.source_FIR_ids[0], self.db)
                    if primary_fir_id:
                        ev = self.db.scalar(select(Evidence).where(Evidence.fir_id == primary_fir_id))
                        if ev:
                            evidence_id = ev.id

                oracle_rel_type = map_relationship_type_to_oracle(rel.relation_type)

                # Check for existing duplicate edge to guarantee idempotency
                existing_rel = self.db.scalar(
                    select(Relationship).where(
                        Relationship.source_entity_id == src_db_id,
                        Relationship.target_entity_id == tgt_db_id,
                        Relationship.relationship_type == oracle_rel_type,
                        Relationship.source_fir_id == primary_fir_id,
                    )
                )
                if not existing_rel:
                    new_rel = Relationship(
                        source_entity_id=src_db_id,
                        target_entity_id=tgt_db_id,
                        relationship_type=oracle_rel_type,
                        confidence=rel.confidence,
                        source_fir_id=primary_fir_id,
                        evidence_id=evidence_id,
                        description=f"{rel.evidence} | source_firs={','.join(rel.source_FIR_ids)} | weight={rel.weight.computed_weight}",
                    )
                    self.db.add(new_rel)
                    created_relationships_count += 1

            # 7b. Persist Analyses (One per evaluated entity)
            created_analyses_count = 0
            entity_analysis_db_map: Dict[int, Analysis] = {}

            for aay_id, risk_score_dict in alerts_payload.get("all_scores", {}).items():
                db_ent_id = id_mapper.get_db_id(aay_id)
                if db_ent_id is None:
                    continue

                ent_metrics = analysis_result.entity_metrics.get(aay_id)
                metrics_json_dict = ent_metrics.model_dump() if ent_metrics else {}

                # Check existing analysis for this entity and case
                existing_analysis = self.db.scalar(
                    select(Analysis).where(
                        Analysis.case_id == case_id,
                        Analysis.entity_id == db_ent_id,
                        Analysis.analysis_type == "GRAPH_INTELLIGENCE_RISK",
                    )
                )
                if not existing_analysis:
                    reasons_text = " | ".join(
                        [f.get("description", "") for f in risk_score_dict.get("contributing_factors", [])]
                    )
                    new_analysis = Analysis(
                        case_id=case_id,
                        entity_id=db_ent_id,
                        analysis_type="GRAPH_INTELLIGENCE_RISK",
                        risk_score=float(risk_score_dict.get("score", 0.0)),
                        risk_level=map_risk_tier_to_oracle(risk_score_dict.get("tier", "LOW")),
                        result_summary=f"Score: {risk_score_dict.get('score')}/100 ({risk_score_dict.get('tier')})",
                        reasons=reasons_text or "Single appearance in network with low risk indicators.",
                        model_version="aayushman-fir-intelligence-v1.0",
                    )
                    self.db.add(new_analysis)
                    self.db.flush()
                    entity_analysis_db_map[db_ent_id] = new_analysis
                    created_analyses_count += 1
                else:
                    entity_analysis_db_map[db_ent_id] = existing_analysis

            # 7c. Persist Alerts (Entity alerts & Cluster alerts)
            created_alerts_count = 0

            # Entity alerts
            for ea in alerts_payload.get("entity_alerts", []):
                target_aay_id = ea.get("target_id")
                db_ent_id = id_mapper.get_db_id(target_aay_id)
                analysis_obj = entity_analysis_db_map.get(db_ent_id) if db_ent_id else None

                existing_alert = self.db.scalar(
                    select(Alert).where(
                        Alert.case_id == case_id,
                        Alert.entity_id == db_ent_id,
                        Alert.alert_type == "HIGH_RISK_ENTITY",
                    )
                )
                if not existing_alert:
                    reasons_summary = "\n".join(ea.get("reasons", []))
                    new_alert = Alert(
                        case_id=case_id,
                        entity_id=db_ent_id,
                        analysis_id=analysis_obj.id if analysis_obj else None,
                        alert_type="HIGH_RISK_ENTITY",
                        severity=map_alert_severity_to_oracle(ea.get("risk_tier", "MEDIUM")),
                        title=f"Elevated Risk Entity: {target_aay_id} (Score: {ea.get('risk_score')})",
                        description=reasons_summary,
                        status=AlertStatus.OPEN,
                    )
                    self.db.add(new_alert)
                    created_alerts_count += 1

            # Cluster alerts
            for ca in alerts_payload.get("cluster_alerts", []):
                comm_target = ca.get("target_id")  # e.g. COMMUNITY-1
                existing_cluster_alert = self.db.scalar(
                    select(Alert).where(
                        Alert.case_id == case_id,
                        Alert.entity_id.is_(None),
                        Alert.title.like(f"%{comm_target}%"),
                    )
                )
                if not existing_cluster_alert:
                    reasons_summary = "\n".join(ca.get("reasons", []))
                    new_cluster_alert = Alert(
                        case_id=case_id,
                        entity_id=None,
                        analysis_id=None,
                        alert_type="ORGANIZED_CRIME_CLUSTER",
                        severity=map_alert_severity_to_oracle(ca.get("risk_tier", "HIGH")),
                        title=f"Suspicious Crime Cluster: {comm_target} (Score: {ca.get('risk_score')})",
                        description=reasons_summary,
                        status=AlertStatus.OPEN,
                    )
                    self.db.add(new_cluster_alert)
                    created_alerts_count += 1

            self.db.commit()

        except Exception as exc:
            self.db.rollback()
            logger.error("Transaction failed during intelligence persistence: %s", exc)
            raise IntelligenceIntegrationError(f"Database error during intelligence persistence: {exc}") from exc

        return {
            "case_id": case_id,
            "entities_evaluated": len(active_entities),
            "relationships_created": created_relationships_count,
            "analyses_created": created_analyses_count,
            "alerts_created": created_alerts_count,
            "graph_metrics": {
                "nodes": graph.number_of_nodes(),
                "edges": graph.number_of_edges(),
                "communities": len(analysis_result.communities),
                "patterns_detected": len(analysis_result.patterns),
            },
            "risk_summary": alerts_payload.get("summary", {}),
            "status": "completed",
        }
