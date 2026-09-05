import json
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.alert import Alert
from app.models.analysis import Analysis
from app.models.case import Case
from app.models.entity import Entity, EntityType
from app.models.evidence import Evidence
from app.models.fir import FIR
from app.models.relationship import Relationship
from app.models.report import Report
from app.schemas.report import ReportListResponse, ReportResponse

router = APIRouter(prefix="/api/reports", tags=["reports"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=ReportListResponse, status_code=status.HTTP_200_OK)
def list_reports(
    db: DbSession,
    case_id: Optional[int] = Query(default=None, gt=0, description="Filter reports by case ID"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> ReportListResponse:
    """Retrieve paginated investigation reports."""
    query = select(Report)
    if case_id is not None:
        query = query.where(Report.case_id == case_id)

    total_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(total_query) or 0

    items = db.scalars(query.order_by(Report.id.desc()).offset(skip).limit(limit)).all()

    return ReportListResponse(
        items=[ReportResponse.model_validate(r) for r in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{report_id}", response_model=ReportResponse, status_code=status.HTTP_200_OK)
def get_report(report_id: int, db: DbSession) -> ReportResponse:
    """Retrieve a single investigation report by ID."""
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportResponse.model_validate(report)


@router.post("/generate/{case_id}", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_case_report(case_id: int, db: DbSession) -> ReportResponse:
    """
    Generates an executive-ready NCRB Criminal Network Investigation Report
    synthesizing Case data, FIRs, Entities, Graph Relationships, Analytics, and Alerts.
    Persists report to Oracle XE reports table.
    """
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found")

    # Aggregate case metrics
    total_firs = db.scalar(select(func.count(FIR.id)).where(FIR.case_id == case_id)) or 0
    total_evidence = db.scalar(select(func.count(Evidence.id)).where(Evidence.case_id == case_id)) or 0

    total_entities = db.scalar(select(func.count(Entity.id)).where(Entity.case_id == case_id)) or 0
    persons_count = db.scalar(select(func.count(Entity.id)).where(Entity.case_id == case_id, Entity.entity_type == EntityType.PERSON)) or 0
    stations_count = db.scalar(select(func.count(Entity.id)).where(Entity.case_id == case_id, Entity.entity_type == EntityType.POLICE_STATION)) or 0
    statutes_count = db.scalar(select(func.count(Entity.id)).where(Entity.case_id == case_id, Entity.entity_type == EntityType.STATUTE)) or 0

    total_relationships = db.scalar(
        select(func.count(Relationship.id))
        .join(Entity, Relationship.source_entity_id == Entity.id)
        .where(Entity.case_id == case_id)
    ) or 0

    total_analyses = db.scalar(select(func.count(Analysis.id)).where(Analysis.case_id == case_id)) or 0
    alerts = list(db.scalars(select(Alert).where(Alert.case_id == case_id).order_by(Alert.id.desc())).all())

    # Build executive report content
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    report_title = f"NCRB Criminal Network Intelligence Report — Case {case.case_number}"

    content = f"""# {report_title}
**Generated At:** {now_str}
**Department:** Ministry of Home Affairs — NCRB, Women Safety Division
**Case Title:** {case.title}
**Case Number:** {case.case_number}
**Status:** {case.status.value if hasattr(case.status, 'value') else case.status}

---

## 1. Executive Summary
This intelligence report synthesizes criminal network extraction, cross-FIR entity resolution, and topological graph analytics across dataset-backed First Information Reports (FIRs).

- **Total FIR Records Analyzed:** {total_firs}
- **Total Evidence Documents:** {total_evidence}
- **Authoritative Canonical Entities:** {total_entities}
  - Persons of Interest / Complainants: {persons_count}
  - Law Enforcement Jurisdictions / Police Stations: {stations_count}
  - Legal Statutes & Criminal Code Sections: {statutes_count}
- **Active Criminal Network Edges (Relationships):** {total_relationships}
- **Topological Entity Risk Evaluations:** {total_analyses}
- **Active Operational Alerts:** {len(alerts)}

---

## 2. Network Graph & Structural Insights
- **Graph Topology:** Multi-relational network formed through structured co-occurrence and statutory overlap.
- **Cross-FIR Associations:** High-frequency topological bridges identify interconnected syndicates and repeated jurisdictional overlap across police boundaries.
- **Entity Resolution Integrity:** Preserves strict cross-FIR person separation to eliminate false-positive mergers, while unifying statutory citations and police station jurisdictions.

---

## 3. High-Priority Alerts & Operational Triggers
"""
    if alerts:
        for idx, alt in enumerate(alerts[:10], 1):
            content += f"- **Alert #{idx} [{alt.severity.value}]** {alt.title}\n  - *Description:* {alt.description or 'No detail provided.'}\n  - *Status:* {alt.status.value}\n"
    else:
        content += "No high-priority alerts triggered for this case scope.\n"

    content += """
---

## 4. Investigative Recommendations
1. **Jurisdictional Coordination:** Focus multi-station task forces on high-degree police station nodes bridging multiple FIR filings.
2. **Statutory Clustering:** Examine recurring penal codes across isolated complainant reports to identify coordinated syndicates.
3. **Evidence Verification:** Utilize mention provenance records to trace every network link back to verified OCR bounding box coordinates in raw evidence.
"""

    report = Report(
        case_id=case_id,
        investigation_id=None,
        report_type="CRIMINAL_NETWORK_SUMMARY",
        title=report_title,
        content=content.strip(),
        generated_by=case.created_by,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return ReportResponse.model_validate(report)
