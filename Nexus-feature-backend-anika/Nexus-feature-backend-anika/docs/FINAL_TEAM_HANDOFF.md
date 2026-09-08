# Nexus SIH Problem Statement 26189 — Final Master Team Handoff
## Truthful Architectural State, System Boundaries & Operational Runbook
**Branch:** `feature/backend-anika` | **Target Base:** `origin/develop` / `origin/main`  
**Database:** Oracle Database 21c Express Edition (XE) | **Alembic Head:** `e8f3b2c1d4a5`

## System Status Declaration
- **BACKEND STATUS:** FROZEN
- **DATABASE:** Oracle XE 21c
- **ALEMBIC:** e8f3b2c1d4a5
- **TESTS:** 107/107 passing
- **DATASET:** 569 images / 544 annotated FIRs / 2,447 OCR records
- **FRONTEND:** Not implemented in backend branch; Krisha owns frontend
- **AUTH/RBAC:** Pending Safina
- **SECURITY AUDIT:** Pending Safina
- **FINAL BRANCH INTEGRATION:** Pending Meet

---

## 1. What Is ALREADY COMPLETE

1. **Raw Dataset Integrity:** 544 annotated FIRs and 2,447 OCR records verified in `Nexus/dataset/FIR_Dataset_ICDAR2023-main` with verified SHA-256 hashes (`693a1e11bd116e2458898e43c48785853b6d6e99439f315b761063c0bb2a357a`).
2. **Oracle XE Ingestion:** 544 `firs` and 544 `evidence` records loaded in Oracle XE with zero duplicate records or orphan foreign keys.
3. **Conservative Entity Resolution:** 804 canonical entities (493 Persons, 11 Police Stations, 300 Statutes) and 1,825 `entity_mention_provenance` records with exact bounding boxes (`bbox_x1..y2`) and character offsets.
4. **Cross-FIR Person Protection:** Same-FIR names are merged; cross-FIR identical names remain isolated (`KEPT_SEPARATE_CROSS_FIR`) to prevent false-positive criminal record linking without official government IDs.
5. **Aayushman Intelligence Bridge:** Phase 2 Graph Construction (804 nodes, 905 edges), Phase 3 Graph Analytics (354 Louvain communities, 73 patterns), and Phase 4 Risk Scoring / Alert Generation (804 entity analyses, 6 alerts including Community 92 and Community 3 cluster alerts).
6. **Transactional Safety & Idempotency:** The entire pipeline executes atomically with rollback protection and is 100% idempotent (rerun creates 0 duplicate relationships, analyses, or alerts).
7. **Grounded Explanation Layer:** `POST /api/intelligence/explain/{id}` generates deterministic factor-based explanations citing degree centrality, community clusters, and statutory co-occurrences without LLM hallucination.
8. **Executive Reporting:** `POST /api/reports/generate/{case_id}` generates real-data NCRB intelligence reports.
9. **Processing Adapter:** `AayushProcessingAdapter` provides frozen handoff conversion and cross-validation against the live database.
10. **Automated Testing Baseline:** **107 / 107 tests passing** (`python -m unittest discover tests`), clean compileall, clean pip check.

---

## 2. What Is NOT Complete

1. **Frontend Implementation:** **NOT YET IMPLEMENTED IN THIS REPOSITORY.** There is no `Nexus/frontend` code committed yet. The frontend API contract and Cytoscape graph endpoints are ready for Krisha.
2. **Authentication / RBAC Enforcement:** **BYPASSED IN PRODUCTION ENDPOINTS.** The routes currently operate open for local SIH evaluator demonstration. JWT bearer token validation and case-level ownership protection must be enforced by Safina.
3. **Formal Cybersecurity Audit:** Penetration testing, automated injection fuzzing, and role-based access checks have not been executed by Safina.
4. **Live Evaluator Rehearsal:** Final walkthrough presentation and live demo execution with the jury must be rehearsed and led by Meet.

---

## 3. Exact Responsibility of Each Teammate

| Member | Focus Area | Core Responsibilities |
| :--- | :--- | :--- |
| **Anika** | Backend & Database | Maintain Oracle XE schema, FastAPI routes, Alembic migrations, database connection pooling. |
| **Krisha** | Frontend & UI | Implement React/Vite dashboard, Cytoscape network graph visualizer, alert triage UI, report viewer. |
| **Aayush** | Evidence Processing | Tune fuzzy matching thresholds in `processing/deduplicator.py`, clean noisy OCR transliterations. |
| **Aayushman**| Intelligence Engine | Tune Louvain community resolution parameters, refine multi-tier risk weights in `scoring.py`. |
| **Safina** | Security & QA | Enforce JWT auth middleware, execute security test matrix, audit file upload boundaries. |
| **Meet** | Integration & AI | Coordinate branch integration into `develop`, lead final live jury demonstration using demo runbook. |

---

## 4. Exact Files Each Teammate Should Modify

- **Krisha:** Create and modify files exclusively under `Nexus/frontend/`.
- **Aayush:** Modify files exclusively under `Nexus/aayush work/PS189/processing/`.
- **Aayushman:** Modify files exclusively under `Nexus/aayushman work/SIH PS189/Aayuushman's work/fir_intelligence/`.
- **Safina:** Add security tests in `Nexus/backend/tests/test_security_vectors.py` and implement JWT middleware in `Nexus/backend/app/core/security.py`.
- **Meet:** Coordinate overall integration, configure demo settings, and update `docs/DEMO_RUNBOOK.md`.
- **Anika:** Maintain `Nexus/backend/app/` routes, schemas, models, and migrations.

---

## 5. Exact Files Each Teammate Must NOT Modify

- **DO NOT TOUCH:** `Nexus/dataset/FIR_Dataset_ICDAR2023-main.zip` or `FIR_details.json` (SHA-256 hashes must remain unmodified).
- **DO NOT TOUCH:** `Nexus/backend/alembic/versions/` (Alembic head is locked at `e8f3b2c1d4a5`).
- **DO NOT TOUCH:** `Nexus/backend/app/database/connection.py` or `base.py`.
- **DO NOT TOUCH:** `Nexus/backend/tests/test_entity_resolution_batch25.py` or `test_entity_resolution_pilot.py` (baseline acceptance suites).

---

## 6. Frozen API Contracts

### A. Graph Visualization: `GET /api/intelligence/graph/{case_id}`
```json
{
  "case_id": 21,
  "nodes": [
    { "id": 1, "label": "Sumita Bera", "type": "PERSON", "confidence": 0.95 },
    { "id": 15, "label": "Airport Police Station", "type": "POLICE_STATION", "confidence": 1.0 }
  ],
  "edges": [
    { "id": 1, "source": 1, "target": 15, "type": "MENTIONED_WITH", "confidence": 1.0, "description": "Co-occurrence in FIR-000" }
  ],
  "total_nodes": 804,
  "total_edges": 905
}
```

### B. Intelligence Pipeline Execution: `POST /api/intelligence/run/{case_id}`
```json
{
  "case_id": 21,
  "entities": 804,
  "relationships_created": 0,
  "analyses_created": 0,
  "alerts_created": 0,
  "status": "completed",
  "graph_metrics": { "nodes": 804, "edges": 905, "communities": 354, "patterns_detected": 73 },
  "risk_summary": { "total_entities_evaluated": 804, "total_entity_alerts": 0, "total_cluster_alerts": 1, "tier_counts": { "HIGH": 0, "MEDIUM": 0, "LOW": 804 }, "min_alert_tier": "MEDIUM" }
}
```

### C. Grounded Factor Explanation: `POST /api/intelligence/explain/{entity_id}`
```json
{
  "entity_id": 47,
  "entity_name": "Airport Police Station",
  "entity_type": "POLICE_STATION",
  "risk_score": 36.2,
  "risk_level": "LOW",
  "explanation": "Entity 'Airport Police Station' is registered as an authoritative law enforcement jurisdiction (POLICE_STATION) with 118 connected incident linkages. It serves as a jurisdictional anchor across distinct FIR filings.",
  "key_factors": [
    "Network Degree: 118 direct topological connection(s) identified",
    "High topological connectivity: acts as a multi-incident cross-FIR hub"
  ],
  "graph_metrics": { "reasons": "Appears across 91 separate FIRs | Acts as a key network broker between clusters (Betweenness 0.0116) | Central controller hub in an unusual star-topology network" },
  "connected_entities_count": 118,
  "alerts": [],
  "confidence": 0.95
}
```

---

## 7. Startup, Testing & Demo Commands

### A. Start Backend
```powershell
cd Nexus/backend
.\venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### B. Run Test Suite
```powershell
cd Nexus/backend
.\venv\Scripts\python.exe -m unittest discover tests
```

### C. Check Compilation & Dependencies
```powershell
cd Nexus/backend
.\venv\Scripts\python.exe -m compileall app scripts tests -q
.\venv\Scripts\pip.exe check
```

### D. Generate Executive NCRB Report
```powershell
curl -X POST http://localhost:8000/api/reports/generate/21
```

---

## 8. Known Limitations & Technical Constraints

1. **Authentication:** Endpoints currently do not mandate a Bearer token so evaluators can test endpoints freely in Swagger UI without token expiry disruptions.
2. **Oracle Case Sensitivity:** Entity lookups utilize `func.lower(normalized_name)` to bypass Oracle uppercase collation subtleties.
3. **Graph Rendering Performance:** Rendering all 804 nodes and 905 edges simultaneously on a single canvas can tax client-side WebGL/Canvas; Krisha should default `limit_nodes` to 200 or allow community filtering.

---

## 9. Integration Order & Git Branch Strategy

1. **Branch Model:** Feature branches (`feature/backend-anika`, `feature/frontend-krisha`, etc.) merge into `develop`.
2. **Integration Sequence:**
   - **Step 1:** Krisha builds frontend against `feature/backend-anika` REST endpoints.
   - **Step 2:** Safina introduces JWT token validation in `app/core/security.py` on a separate branch without breaking test discovery.
   - **Step 3:** Aayush and Aayushman verify processing and intelligence tuning via cross-validation and pipeline execution endpoints.
   - **Step 4:** Meet merges all branches into `develop` and validates the end-to-end demo flow.
