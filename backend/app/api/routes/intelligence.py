import json
from typing import Annotated, Any, Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.alert import Alert
from app.models.analysis import Analysis
from app.models.case import Case
from app.models.entity import Entity
from app.models.relationship import Relationship
from app.services.intelligence_integration_service import (
    CaseNotFoundError,
    IntelligenceIntegrationError,
    IntelligenceIntegrationService,
)

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])
DbSession = Annotated[Session, Depends(get_db)]


class RunIntelligenceResponse(BaseModel):
    case_id: int
    entities: int
    relationships_created: int
    analyses_created: int
    alerts_created: int
    status: str
    graph_metrics: Dict[str, Any] = Field(default_factory=dict)
    risk_summary: Dict[str, Any] = Field(default_factory=dict)


class GraphNode(BaseModel):
    id: int
    label: str
    type: str
    confidence: Optional[float] = None


class GraphEdge(BaseModel):
    id: int
    source: int
    target: int
    type: str
    confidence: Optional[float] = None
    description: Optional[str] = None


class NetworkGraphResponse(BaseModel):
    case_id: int
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_nodes: int
    total_edges: int


class EntityExplanationResponse(BaseModel):
    entity_id: int
    entity_name: str
    entity_type: str
    risk_score: float
    risk_level: str
    explanation: str
    key_factors: List[str]
    graph_metrics: Dict[str, Any]
    connected_entities_count: int
    alerts: List[Dict[str, Any]]
    confidence: float = 0.95


@router.post("/run/{case_id}", response_model=RunIntelligenceResponse, status_code=status.HTTP_200_OK)
def run_case_intelligence(
    case_id: int,
    db: DbSession,
    image_ids: Optional[str] = Query(
        default=None,
        description="Comma-separated dataset image IDs to limit scope (e.g. '0,1,2,3,4')",
    ),
) -> RunIntelligenceResponse:
    target_ids: Optional[Set[int]] = None
    if image_ids:
        try:
            target_ids = {int(x.strip()) for x in image_ids.split(",") if x.strip()}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid image_ids parameter; must be comma-separated integers.") from exc

    service = IntelligenceIntegrationService(db)
    try:
        res = service.run_intelligence_pipeline(case_id=case_id, requested_image_ids=target_ids)
        return RunIntelligenceResponse(
            case_id=res["case_id"],
            entities=res["entities_evaluated"],
            relationships_created=res["relationships_created"],
            analyses_created=res["analyses_created"],
            alerts_created=res["alerts_created"],
            status=res["status"],
            graph_metrics=res.get("graph_metrics", {}),
            risk_summary=res.get("risk_summary", {}),
        )
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IntelligenceIntegrationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/graph/{case_id}", response_model=NetworkGraphResponse, status_code=status.HTTP_200_OK)
def get_network_graph(
    case_id: int,
    db: DbSession,
    limit_nodes: int = Query(default=500, ge=1, le=2000, description="Max nodes to return for visualization"),
) -> NetworkGraphResponse:
    """
    Returns nodes and edges formatted directly for Cytoscape/Vis.js frontend graph visualizer.
    """
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found")

    entities = list(db.scalars(select(Entity).where(Entity.case_id == case_id).limit(limit_nodes)).all())
    entity_id_set = {e.id for e in entities}

    relationships = list(db.scalars(
        select(Relationship).where(
            Relationship.source_entity_id.in_(entity_id_set),
            Relationship.target_entity_id.in_(entity_id_set),
        )
    ).all())

    nodes = [
        GraphNode(
            id=e.id,
            label=e.name,
            type=e.entity_type.value if hasattr(e.entity_type, "value") else str(e.entity_type),
            confidence=e.confidence,
        )
        for e in entities
    ]

    edges = [
        GraphEdge(
            id=r.id,
            source=r.source_entity_id,
            target=r.target_entity_id,
            type=r.relationship_type.value if hasattr(r.relationship_type, "value") else str(r.relationship_type),
            confidence=r.confidence,
            description=r.description,
        )
        for r in relationships
    ]

    return NetworkGraphResponse(
        case_id=case_id,
        nodes=nodes,
        edges=edges,
        total_nodes=len(nodes),
        total_edges=len(edges),
    )


@router.post("/explain/{entity_id}", response_model=EntityExplanationResponse, status_code=status.HTTP_200_OK)
def explain_entity_risk(
    entity_id: int,
    db: DbSession,
) -> EntityExplanationResponse:
    """
    Phase 11 (Meet / AI Explanation Layer):
    Synthesizes computed graph metrics, relationships, and risk scores into an
    explainable, evidence-grounded intelligence summary.
    """
    entity = db.get(Entity, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity with ID {entity_id} not found")

    # Fetch Analysis record
    analysis = db.scalar(
        select(Analysis)
        .where(Analysis.entity_id == entity_id, Analysis.analysis_type == "GRAPH_INTELLIGENCE_RISK")
        .order_by(Analysis.id.desc())
    )

    # Fetch connected relationships
    connected_rels = list(db.scalars(
        select(Relationship).where(
            (Relationship.source_entity_id == entity_id) | (Relationship.target_entity_id == entity_id)
        )
    ).all())

    # Fetch alerts
    alerts = list(db.scalars(
        select(Alert).where(Alert.entity_id == entity_id).order_by(Alert.id.desc())
    ).all())

    # Graph metrics
    risk_score = analysis.risk_score if analysis and analysis.risk_score is not None else 10.0
    risk_level = analysis.risk_level.value if analysis and analysis.risk_level else "LOW"

    metrics_payload = {}
    if analysis and analysis.reasons:
        try:
            metrics_payload = json.loads(analysis.reasons)
        except Exception:
            metrics_payload = {"raw_reasons": analysis.reasons}
    elif analysis and analysis.result_summary:
        metrics_payload = {"summary": analysis.result_summary}

    # Factor synthesis
    key_factors: List[str] = []
    deg = len(connected_rels)
    key_factors.append(f"Network Degree: {deg} direct topological connection(s) identified")

    if deg > 10:
        key_factors.append("High topological connectivity: acts as a multi-incident cross-FIR hub")
    elif deg > 2:
        key_factors.append("Moderate topological connectivity: involved in multi-entity incident clusters")
    else:
        key_factors.append("Isolated or low-degree connection in current evidence scope")

    if alerts:
        key_factors.append(f"Associated with {len(alerts)} operational alert(s)")

    ent_type_str = entity.entity_type.value if hasattr(entity.entity_type, "value") else str(entity.entity_type)

    if ent_type_str == "POLICE_STATION":
        explanation = (
            f"Entity '{entity.name}' is registered as an authoritative law enforcement jurisdiction "
            f"({ent_type_str}) with {deg} connected incident linkages. It serves as a jurisdictional "
            f"anchor across distinct FIR filings."
        )
    elif ent_type_str == "STATUTE":
        explanation = (
            f"Entity '{entity.name}' represents a legal penal statute ({ent_type_str}) invoked across "
            f"{deg} separate complaints and police proceedings. Structural co-occurrence indicates recurring "
            f"statutory patterns across FIRs."
        )
    else:
        explanation = (
            f"Subject '{entity.name}' ({ent_type_str}) has {deg} recorded relationship(s) in this case. "
            f"Topological analysis indicates {risk_level} risk profile based on network centrality and "
            f"evidence corroboration."
        )

    return EntityExplanationResponse(
        entity_id=entity.id,
        entity_name=entity.name,
        entity_type=ent_type_str,
        risk_score=risk_score,
        risk_level=risk_level,
        explanation=explanation,
        key_factors=key_factors,
        graph_metrics=metrics_payload,
        connected_entities_count=deg,
        alerts=[
            {
                "id": a.id,
                "title": a.title,
                "severity": a.severity.value,
                "status": a.status.value,
                "description": a.description,
            }
            for a in alerts
        ],
        confidence=0.95,
    )
