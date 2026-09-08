# Nexus Architecture Document
## Problem Statement 26189 — AI-Powered Criminal Network Analysis System
**Organization:** Ministry of Home Affairs | **Department:** NCRB, Women Safety Division  
**Stack:** FastAPI + SQLAlchemy + Oracle Database 21c XE + NetworkX + Louvain

---

## 1. System Topology & Information Flow

The Nexus architecture follows a strict, unidirectional, evidence-grounded pipeline that completely eliminates synthetic or hallucinatory criminal network construction.

```
+-----------------------------------------------------------------------------------+
|                            1. DATA INGESTION & OCR                                |
|  - Source: 544 Usable First Information Reports (ICDAR 2023 dataset)              |
|  - Raw OCR: 2,447 Records across 4 categories (0: Station, 1: Year, 2: Statute,   |
|    3: Complainant/Person)                                                         |
|  - Hash Integrity: SHA-256 verified (FIR_details.json)                            |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        2. ORACLE XE 21c AUTHORITATIVE STORE                       |
|  - firs table: 544 Records (Metadata, FIR number, dataset image ID)               |
|  - evidence table: 544 Records (Extracted OCR text payload, hash, MIME type)      |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                    3. CONSERVATIVE EXTRACTION & RESOLUTION                        |
|  - Extractor: 1,825 Raw mentions extracted with exact character offsets & bboxes  |
|  - Resolver: Merges same-FIR mentions; unifies statutes & police stations across  |
|    FIRs; isolates cross-FIR person mentions (KEPT_SEPARATE_CROSS_FIR)             |
|  - Storage: 804 Canonical Entities, 1,825 EntityMentionProvenance records         |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                 4. AAYUSHMAN INTELLIGENCE & GRAPH ENGINE (PHASES 2-4)             |
|  - Phase 2 (GraphBuilder): 804 Nodes, 905 Edges (Structured & Co-occurrence)     |
|  - Phase 3 (Analytics): 354 Louvain Communities, 73 Topological Graph Patterns    |
|  - Phase 4 (Scoring & Alerts): 804 Topological Entity Risk Analyses, Cluster      |
|    Alerts (Community 92)                                                          |
|  - Storage: relationships (905), analyses (804), alerts (6) in Oracle XE          |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                      5. MEET AI EXPLANATION & REPORT ENGINE                       |
|  - Explanation Layer: Grounded, factor-based synthesis of centrality & risk       |
|  - Investigation Reports: Formatted executive NCRB summaries in reports table     |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                       6. REST API & FRONTEND CONSUMPTION                          |
|  - Backend: FastAPI REST service with full CORS enabled                           |
|  - Endpoints: /api/cases, /api/firs, /api/entities, /api/relationships,           |
|    /api/intelligence/run/{case_id}, /api/intelligence/graph/{case_id},            |
|    /api/alerts, /api/reports, /api/processing                                     |
|  - Frontend: Krisha React Dashboard (Network visualization & Investigation suite)  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Core Relational Schema (Oracle XE 21c)

1. **`firs`**: Core FIR metadata (case_id, fir_number, police_station, incident_date, dataset_image_id).
2. **`evidence`**: Case evidence payload (case_id, fir_id, file_path, file_hash, extracted_text).
3. **`entities`**: Canonical entities (case_id, entity_type, name, normalized_name, confidence).
4. **`entity_mention_provenance`**: Unbroken audit trail linking canonical entities to raw evidence (entity_id, evidence_id, matched_text, start_char, end_char, bbox_x1..y2, ocr_confidence).
5. **`relationships`**: Network graph edges (source_entity_id, target_entity_id, relationship_type, confidence, source_fir_id, evidence_id, description).
6. **`analyses`**: Risk scoring evaluations (case_id, entity_id, analysis_type, risk_score, risk_level, result_summary, reasons).
7. **`alerts`**: High-priority investigative triggers (case_id, entity_id, analysis_id, alert_type, severity, title, status).
8. **`reports`**: Formatted investigative intelligence reports (case_id, report_type, title, content, generated_by).
9. **`investigations`**: Case investigation tracking records (case_id, investigator_id, status, notes).
10. **`users`**: Administrative and operational investigator accounts (username, email, hashed_password, role).

---

## 3. Teammate Module Decoupling & Boundaries

| Member | Domain | Contract Input | Contract Output | Strict Prohibitions |
| :--- | :--- | :--- | :--- | :--- |
| **Anika** | Backend & Database | Raw Dataset & Config | REST API & Oracle Schema | Do NOT bypass Oracle schema constraints or delete test suites. |
| **Krisha** | Frontend & UI | REST API Endpoints | Interactive Dashboard | Do NOT invent mock API responses; consume real FastAPI endpoints. |
| **Aayush** | Evidence Processing | Raw OCR JSON | `StructuredFIR` JSON | Do NOT overwrite backend mention provenance or drop category 2/3. |
| **Aayushman**| Intelligence Engine | Canonical Entities & Provenances | NetworkX Graph, Risk & Alerts | Do NOT run synthetic Phase 1 mock extractor in production. |
| **Safina** | Security & QA | Test Cases & Security Vectors | Audit Reports & Test Automation | Do NOT alter production database schema or disable security checks. |
| **Meet** | Integration & AI | Graph Metrics & Analytics | Factor Explanations & Reports | Do NOT allow LLM to hallucinate risk scores independently of graph. |
