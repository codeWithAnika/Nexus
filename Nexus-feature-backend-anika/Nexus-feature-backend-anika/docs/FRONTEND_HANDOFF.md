# Nexus Frontend Handoff Guide
## For: Krisha (Frontend & Dashboard Lead)
**Backend Base URL:** `http://localhost:8000`  
**CORS Status:** Enabled (`allow_origins=["*"]`)  
**Auth Headers:** Ready for Bearer token or direct access in demo mode.

---

## 1. What to Work On
- Build the single-page or multi-view React/Vite dashboard.
- Connect UI views directly to the live FastAPI endpoints.
- Build the Interactive Criminal Network Canvas (using **Cytoscape.js**, **vis-network**, or **@xyflow/react**).
- Build the Entity Detail Drawer displaying exact OCR bounding boxes and mention snippets.
- Build the Alert Triage and Case Report Viewer.

## 2. What NOT to Touch
- Do **NOT** invent mock data or hardcoded mock API responses.
- Do **NOT** touch `Nexus/backend/`, `alembic/`, or database connection strings.
- Do **NOT** modify the raw dataset files in `Nexus/dataset/`.

---

## 3. Recommended Navigation & Page Flow

```
[Login Screen]
      │
      ▼
[Operations Dashboard] ──► KPI Cards: Total FIRs (544), Entities (804), Alerts (6), Graph Edges (905)
      │
      ▼
[Case Details (Case 21)]
      ├─► [Evidence Tab] ──► List FIRs & OCR Evidence Documents
      ├─► [Network Graph Tab] ──► Full Cytoscape Graph Canvas with node click handlers
      ├─► [Entities Tab] ──► Searchable list of Persons, Police Stations, Statutes
      ├─► [Alerts Tab] ──► Triage Open Alerts & Acknowledge/Resolve
      └─► [Reports Tab] ──► View Executive NCRB Intelligence Summary & Download Markdown
```

---

## 4. Exact API Endpoints to Call

### A. Graph Visualization
- **Endpoint:** `GET /api/intelligence/graph/21?limit_nodes=500`
- **Payload Shape:**
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
- **Node Coloring Suggestion:**
  - `PERSON`: Orange / Red (`#E53935`)
  - `POLICE_STATION`: Navy / Cyan (`#1E88E5`)
  - `STATUTE`: Purple / Amber (`#8E24AA`)

### B. Entity Details & OCR Provenance
- Click a node in the graph $\rightarrow$ Call:
  1. `GET /api/entities/{entity_id}`: Entity details.
  2. `GET /api/entities/{entity_id}/mentions`: Returns bounding boxes (`bbox_x1, bbox_y1, bbox_x2, bbox_y2`) and character offsets for overlay on FIR scans!
  3. `POST /api/intelligence/explain/{entity_id}`: Returns grounded AI factor explanation.

### C. Trigger Live Intelligence Analysis
- **Endpoint:** `POST /api/intelligence/run/21`
- Triggers Phase 2-4 graph construction, community detection, and risk scoring. Returns updated graph metrics and risk summary.

### D. Alert Management
- **List Alerts:** `GET /api/alerts?case_id=21`
- **Update Alert Status:** `PUT /api/alerts/{alert_id}/status`
  - Body: `{"status": "ACKNOWLEDGED"}` or `{"status": "RESOLVED"}`

### E. Case Intelligence Report
- **List Reports:** `GET /api/reports?case_id=21`
- **Generate Fresh Report:** `POST /api/reports/generate/21`
  - Returns executive markdown report formatted for NCRB officers.
