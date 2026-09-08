# Nexus Master Integration & AI Handoff Guide
## For: Meet (Architecture, Integration, AI & Final Demo Lead)

---

## 1. End-to-End System Flow

```
[User Browser]
      │
      ▼
[Krisha Frontend Dashboard (React/Vite)]
      │
      ▼ HTTP REST (JSON)
[Anika Backend API (FastAPI)]
      │
      ├──► Reads/Writes ──► [Oracle Database 21c XE]
      │                         (FIRs, Evidence, Canonical Entities, Provenance)
      │
      ├──► Adapter Bridge ──► [Aayushman Intelligence Engine]
      │                         Phase 2: GraphBuilder (804 Nodes, 905 Edges)
      │                         Phase 3: Louvain Communities (354), Patterns (73)
      │                         Phase 4: Risk Scoring & Alerts (Community 92)
      │
      ├──► Advisory Hook ──► [Meet AI Explanation Engine]
      │                         Grounded factor synthesis without hallucinatory scoring
      │
      └──► Adapter Bridge ──► [Aayush Processing]
                                Standalone Structured Evidence Cross-Validation
```

---

## 2. Meet / AI Explanation Layer Architecture

The development plan explicitly stipulates:
> **Core Detection:** Deterministic rule and graph topological engine.  
> **AI Explanation Layer:** Explain and ground *why* an entity or syndicate was flagged. The AI must **never** make unsupported criminal determinations independently of graph evidence.

### Explanation Endpoint
- **URL:** `POST http://localhost:8000/api/intelligence/explain/{entity_id}`
- **Inputs Evaluated:**
  - Entity Type (`PERSON`, `POLICE_STATION`, `STATUTE`)
  - Degree Centrality (direct topological connections)
  - Louvain Community Membership
  - Associated Operational Alerts
  - Co-occurrence frequency across FIRs
- **Output:** Grounded explanation narrative, structured key factors array, and high-confidence metrics payload.

---

## 3. Environment Setup & Startup Sequence

### A. Prerequisites
- Python 3.11+ / 3.14 (Virtualenv installed at `Nexus/backend/venv`)
- Oracle XE 21c running on `localhost:1521/XEPDB1`
- Credentials configured in `Nexus/backend/.env`:
  ```env
  DATABASE_URL=oracle+oracledb://nexus:nexus_password@localhost:1521/?service_name=XEPDB1
  SECRET_KEY=nexus-super-secret-production-key-sih-2026
  ```

### B. Launching Backend
```powershell
cd Nexus/backend
.\venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### C. Launching Frontend (Krisha)
```powershell
cd Nexus/frontend
npm install
npm run dev
```

---

## 4. Official SIH Demo Sequence (Meet's Walkthrough Script)

1. **System Health & Preflight:**
   - Open `http://localhost:8000/health` $\rightarrow$ Confirm `{"status": "healthy"}`.
2. **Operations Dashboard Overview:**
   - Show Case 21 (`NEXUS-FIR-IMPORT-001`): 544 FIRs ingested from official ICDAR 2023 dataset.
3. **Entity Resolution & Provenance Demonstration:**
   - Show 804 canonical entities.
   - Click on *Sumita Bera* or *Airport Police Station*.
   - Call `GET /api/entities/{id}/mentions` to display raw OCR bounding boxes on the FIR scan.
   - Highlight the **conservative identity separation rule**: explain why cross-FIR persons are separated to prevent false criminal linking.
4. **Interactive Criminal Network Visualizer:**
   - Open Network Graph view (`GET /api/intelligence/graph/21`).
   - Display 804 nodes and 905 edges colored by type.
   - Point out high-degree jurisdictional hubs (*Airport Police Station*) bridging multiple FIR complaints.
5. **Topological Intelligence & Alerts:**
   - Trigger `POST /api/intelligence/run/21`.
   - Show execution completing in ~1.2 seconds across all 544 FIRs.
   - Display detected Louvain communities (354) and the priority **Cluster Alert (Community 92)**.
6. **Explainable AI Breakdown:**
   - Call `POST /api/intelligence/explain/{entity_id}`.
   - Show how the explanation cites real graph centrality, degree, and co-occurrence without hallucination.
7. **Executive Investigation Report:**
   - Call `POST /api/reports/generate/21`.
   - Display the generated NCRB Criminal Network Investigation Report ready for senior police leadership.
