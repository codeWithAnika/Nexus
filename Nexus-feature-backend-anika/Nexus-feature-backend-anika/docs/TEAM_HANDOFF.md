# Nexus SIH PS26189 — Master Six-Member Team Handoff Specification

**Problem Statement:** 26189 — AI-Powered Criminal Network Analysis System  
**Organization:** Ministry of Home Affairs / NCRB, Women Safety Division  
**Frozen Baseline Branch:** `feature/backend-anika`  
**Target Integration Branch:** `develop` / `main`  
**Alembic Head:** `e8f3b2c1d4a5` | **Test Suite:** 107/107 Passing  
**Status Date:** 2026-09-06  

---

## 1. Six-Member Ownership Matrix

| Member | Focus Area | Branch Name | Primary Files & Directory Scope |
| :--- | :--- | :--- | :--- |
| **Anika** | Backend & Database | `feature/backend-anika` | `Nexus/backend/app/`, `Nexus/backend/alembic/`, `Nexus/backend/tests/` |
| **Krisha** | Frontend & UI | `feature/frontend-krisha` | `Nexus/frontend/` (React, Vite, Cytoscape, Tailwind) |
| **Aayush** | Evidence & OCR Processing | `feature/processing-aayush` | `Nexus/aayush work/PS189/processing/` |
| **Aayushman** | Intelligence & Graph Analytics | `feature/intelligence-aayushman`| `Nexus/aayushman work/SIH PS189/Aayuushman's work/fir_intelligence/` |
| **Safina** | Security, Auth & QA | `feature/security-safina` | `Nexus/backend/app/core/security.py`, `Nexus/backend/tests/test_security_vectors.py` |
| **Meet** | Integration & Live Demo | `feature/integration-meet` | `docs/DEMO_RUNBOOK.md`, `docs/MEET_INTEGRATION_HANDOFF.md`, branch coordination |

---

## 2. Truthful Module Readiness Status

| Module / Layer | Implementation Status | Responsible | Current Verification State |
| :--- | :--- | :--- | :--- |
| **Raw Dataset & Checksums** | `COMPLETE` | Anika / Aayush | 544 FIRs, 2,447 OCR records, SHA-256 verified |
| **Oracle XE Schema & Models** | `COMPLETE` | Anika | Locked at Alembic `e8f3b2c1d4a5`, zero orphans/duplicates |
| **Entity Extraction & Resolution**| `COMPLETE` | Anika | 804 entities, 1,825 provenances, cross-FIR protection |
| **Aayushman Intelligence Bridge** | `COMPLETE` | Anika / Aayushman | 905 edges, 354 communities, 73 patterns, 6 alerts |
| **Deterministic Grounded Explanations**| `COMPLETE` | Anika | Factor-based degree, community, and statute trails |
| **Executive NCRB Reporting** | `COMPLETE` | Anika | Markdown and JSON intelligence dossiers generated |
| **Automated Backend Regression Tests**| `COMPLETE` | Anika | **107 / 107 tests passing** (8.9s execution time) |
| **Frozen API Contracts** | `READY FOR TEAM` | Anika | Documented in `docs/API_CONTRACT.md` |
| **Frontend Web Dashboard** | `NOT IMPLEMENTED` | Krisha | No frontend code in repo; contracts and schemas ready |
| **Aayush Processing Refinements**| `READY FOR TEAM` | Aayush | Independent reference output verified (67.91% semantic overlap) |
| **Aayushman Algorithm Tuning** | `READY FOR TEAM` | Aayushman | Weights and thresholds accessible in config |
| **Authentication & RBAC Enforcement**| `NEEDS TEAM WORK` | Safina | Auth bypassed for local demo; JWT enforcement needed |
| **Security Audit & Fuzzing** | `NEEDS TEAM WORK` | Safina | Penetration testing and OWASP checklist pending |
| **Live Evaluator Demonstration** | `NEEDS TEAM WORK` | Meet | Rehearsal and multi-branch merge coordination pending |

---

## 3. Strict Modification Boundaries

### Allowed Modifications
- **Krisha:** Build React/Vite dashboard inside `Nexus/frontend/`.
- **Aayush:** Refine extraction heuristics inside `Nexus/aayush work/`.
- **Aayushman:** Fine-tune scoring weights inside `Nexus/aayushman work/`.
- **Safina:** Add security tests in `Nexus/backend/tests/` and enable JWT middleware in `Nexus/backend/app/core/security.py`.
- **Meet:** Manage merge conflicts and maintain `docs/DEMO_RUNBOOK.md`.

### Forbidden Modifications (DO NOT TOUCH)
- **DO NOT TOUCH:** `Nexus/dataset/` — The raw FIR dataset and checksums are immutable.
- **DO NOT TOUCH:** `Nexus/backend/alembic/` — The database migration state is locked at `e8f3b2c1d4a5`.
- **DO NOT TOUCH:** `Nexus/backend/app/database/` — Connection pooling and base declarative models are frozen.
- **DO NOT TOUCH:** `Nexus/backend/tests/test_entity_resolution_*.py` — Baseline entity resolution regression suites must not be altered.

---

## 4. Key Endpoints for Team Integration

| Purpose | Method & Endpoint | Payload / Params | Expected Response |
| :--- | :--- | :--- | :--- |
| **Network Graph (Cytoscape)** | `GET /api/intelligence/graph/{case_id}` | `case_id=21` | `{nodes: [...], edges: [...], total_nodes: 804, total_edges: 905}` |
| **Alert Triage** | `GET /api/alerts?case_id={id}` | `case_id=21`, `severity=HIGH` | Array of 6 alerts (Community 92, Community 3, and top entities) |
| **Entity Factor Explanation** | `POST /api/intelligence/explain/{entity_id}` | `entity_id=47` | Deterministic explanation citing centrality, community & statutes |
| **Intelligence Pipeline Run** | `POST /api/intelligence/run/{case_id}` | `case_id=21` | Idempotent graph build, analysis & scoring results |
| **Executive NCRB Report** | `POST /api/reports/generate/{case_id}` | `case_id=21` | Formatted intelligence report with executive summary |

---

## 5. Verification Gate for All Teammates

Before opening any Pull Request against `develop`, every team member must execute and verify:
```powershell
cd Nexus/backend
.\venv\Scripts\python.exe -m unittest discover tests
```
**Required Result:** `Ran 107 tests in ~9s - OK`.
