# Nexus — AI-Powered Criminal Network Analysis System
### Smart India Hackathon (SIH) — Problem Statement 26189
**Organization:** Ministry of Home Affairs | **Department:** NCRB, Women Safety Division  
**Repository Branch:** `feature/backend-anika`

---

## Executive Overview

**Nexus** is an enterprise-grade criminal intelligence platform designed for law enforcement agencies to uncover hidden syndicate connections, repeat offenders, and jurisdictional nexus points across First Information Reports (FIRs).

Nexus integrates raw scanned police documentation, deterministic entity resolution, topological graph theory, and explainable AI into a unified, evidence-grounded investigative dashboard.

---

## Key System Metrics (Live Production Dataset)

- **Dataset Source:** Official ICDAR 2023 FIR Dataset (`FIR_Dataset_ICDAR2023`)
- **FIRs Ingested:** 544 FIRs across 569 images
- **OCR Records Analyzed:** 2,447 records across 4 semantic categories
- **Authoritative Canonical Entities:** 804 (491 Persons, 300 Statutes, 13 Police Stations)
- **Mention Provenance Records:** 1,825 unbroken bounding boxes and character spans
- **Criminal Network Edges:** 905 topological connections
- **Louvain Communities Detected:** 354 distinct syndicates & co-offending cliques
- **Topological Patterns:** 73 structural crime patterns
- **Active Operational Alerts:** 6 alerts (including High-Density Community Cluster 92)
- **Test Suite Status:** 107 / 107 Unit & Integration Tests Passing (100% Green)

---

## 6-Member Team Structure & Ownership

| Member | Focus Area | Primary Deliverables | Handoff Guide |
| :--- | :--- | :--- | :--- |
| **Anika** | Backend & Database | FastAPI REST API, Oracle XE 21c, Alembic Migrations | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| **Krisha** | Frontend & UI | React/Vite Dashboard, Cytoscape Network Visualizer | [`docs/FRONTEND_HANDOFF.md`](docs/FRONTEND_HANDOFF.md) |
| **Aayushman**| Intelligence Engine | Graph Analytics, Louvain Clustering, Risk Scoring | [`docs/INTELLIGENCE_HANDOFF.md`](docs/INTELLIGENCE_HANDOFF.md) |
| **Aayush** | Evidence Processing| Standalone OCR Cleaning, RapidFuzz Deduplication | [`docs/PROCESSING_HANDOFF.md`](docs/PROCESSING_HANDOFF.md) |
| **Safina** | Security & QA | Security Vector Defense, Test Automation, RBAC | [`docs/SECURITY_QA_HANDOFF.md`](docs/SECURITY_QA_HANDOFF.md) |
| **Meet** | Integration & AI | Master Architecture, Grounded AI Explanation, Demo | [`docs/INTEGRATION_HANDOFF.md`](docs/INTEGRATION_HANDOFF.md) |

---

## Quick Start Guide

### 1. Launch Backend (FastAPI + Oracle XE)
```powershell
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*API Documentation:* Open `http://localhost:8000/docs` for interactive Swagger UI.

### 2. Run Test Suite
```powershell
cd backend
.\venv\Scripts\python.exe -m unittest discover tests
```

### 3. Core API Endpoints
- **System Health:** `GET http://localhost:8000/health`
- **Network Graph Canvas:** `GET http://localhost:8000/api/intelligence/graph/21`
- **Run Pipeline:** `POST http://localhost:8000/api/intelligence/run/21`
- **AI Explanation:** `POST http://localhost:8000/api/intelligence/explain/{entity_id}`
- **Executive Report:** `POST http://localhost:8000/api/reports/generate/21`
- **Aayush Cross-Validation:** `GET http://localhost:8000/api/processing/cross-validate`

---

## Documentation Library

- **[Master Architecture](docs/ARCHITECTURE.md)**: System topology, relational schema, and component flow.
- **[API Contract](docs/API_CONTRACT.md)**: Exhaustive REST endpoint specifications with sample request/response JSONs.
- **[Data Pipeline](docs/DATA_PIPELINE.md)**: OCR categories, entity resolution rules, and provenance preservation.
- **[Demo Runbook](docs/DEMO_RUNBOOK.md)**: Operator instructions and live evaluator demonstration sequence.
- **[Team Branching](docs/TEAM_BRANCHING.md)**: Git workflow and contribution guidelines.
