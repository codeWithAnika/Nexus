# Nexus API Contract & Specification
## Base URL: `http://localhost:8000`
**Content-Type:** `application/json`  
**CORS:** Enabled for all origins (`*`)  

---

## 1. System Health

### `GET /health`
- **Description:** Checks server health and readiness.
- **Request:** None
- **Response (200 OK):**
```json
{
  "status": "healthy"
}
```

---

## 2. Cases

### `GET /api/cases`
- **Query Parameters:** `skip` (int, default 0), `limit` (int, default 100)
- **Response (200 OK):**
```json
[
  {
    "id": 21,
    "case_number": "NEXUS-FIR-IMPORT-001",
    "title": "Dataset FIR Ingestion Batch 2026-03-05",
    "description": "Auto-generated ingestion case for FIR_details.json dataset import",
    "status": "ACTIVE",
    "created_by": 32,
    "created_at": "2026-09-05T13:47:00Z"
  }
]
```

### `GET /api/cases/{case_id}`
- **Path Parameters:** `case_id` (int)
- **Response (200 OK):** Single Case object
- **Error (404 Not Found):** `{"detail": "Case not found"}`

---

## 3. First Information Reports (FIRs)

### `GET /api/firs`
- **Query Parameters:** `case_id` (optional int), `skip` (int, default 0), `limit` (int, default 50)
- **Response (200 OK):**
```json
{
  "items": [
    {
      "id": 575,
      "case_id": 21,
      "fir_number": "FIR-000",
      "police_station": "Airport Police Station",
      "incident_date": "2020-01-01T00:00:00Z",
      "dataset_image_id": 0,
      "created_at": "2026-09-05T13:47:00Z"
    }
  ],
  "total": 544,
  "skip": 0,
  "limit": 50
}
```

---

## 4. Canonical Entities & Mentions

### `GET /api/entities`
- **Query Parameters:** `case_id` (optional int), `entity_type` (optional enum: `PERSON`, `POLICE_STATION`, `STATUTE`), `skip` (int), `limit` (int)
- **Response (200 OK):**
```json
{
  "items": [
    {
      "id": 1,
      "case_id": 21,
      "entity_type": "PERSON",
      "name": "Sumita Bera",
      "normalized_name": "Sumita Bera",
      "confidence": 0.95,
      "created_at": "2026-09-05T14:10:00Z"
    }
  ],
  "total": 804,
  "skip": 0,
  "limit": 50
}
```

### `GET /api/entities/{entity_id}/mentions`
- **Description:** Returns the exact OCR bounding box coordinates and character span provenance.
- **Path Parameters:** `entity_id` (int)
- **Response (200 OK):**
```json
[
  {
    "id": 101,
    "entity_id": 1,
    "evidence_id": 575,
    "matched_text": "Sumita Bera",
    "start_char": 24,
    "end_char": 35,
    "ocr_confidence": 0.92,
    "source_index": 0,
    "bbox_x1": 120.0,
    "bbox_y1": 450.0,
    "bbox_x2": 310.0,
    "bbox_y2": 480.0
  }
]
```

---

## 5. Network Relationships & Graph Visualizer

### `GET /api/relationships`
- **Query Parameters:** `case_id` (optional int), `entity_id` (optional int), `skip` (int), `limit` (int)
- **Response (200 OK):**
```json
{
  "items": [
    {
      "id": 1,
      "source_entity_id": 1,
      "target_entity_id": 15,
      "relationship_type": "MENTIONED_WITH",
      "confidence": 1.0,
      "source_fir_id": 575,
      "evidence_id": 575,
      "description": "Co-occurrence in FIR-000",
      "created_at": "2026-09-05T19:00:00Z"
    }
  ],
  "total": 905,
  "skip": 0,
  "limit": 100
}
```

### `GET /api/intelligence/graph/{case_id}`
- **Description:** Optimized for direct consumption by Cytoscape / Vis.js / React Flow network canvas.
- **Query Parameters:** `limit_nodes` (int, default 500)
- **Response (200 OK):**
```json
{
  "case_id": 21,
  "nodes": [
    {
      "id": 1,
      "label": "Sumita Bera",
      "type": "PERSON",
      "confidence": 0.95
    },
    {
      "id": 15,
      "label": "Airport Police Station",
      "type": "POLICE_STATION",
      "confidence": 1.0
    }
  ],
  "edges": [
    {
      "id": 1,
      "source": 1,
      "target": 15,
      "type": "MENTIONED_WITH",
      "confidence": 1.0,
      "description": "Co-occurrence in FIR-000"
    }
  ],
  "total_nodes": 804,
  "total_edges": 905
}
```

---

## 6. Intelligence Execution & AI Explanation

### `POST /api/intelligence/run/{case_id}`
- **Description:** Runs Aayushman's Phase 2 Graph Construction, Phase 3 Analytics, and Phase 4 Risk Scoring. Transactional & Idempotent.
- **Query Parameters:** `image_ids` (optional comma-separated string, e.g. `0,1,2,3,4` for pilot test)
- **Response (200 OK):**
```json
{
  "case_id": 21,
  "entities": 804,
  "relationships_created": 0,
  "analyses_created": 0,
  "alerts_created": 0,
  "status": "completed",
  "graph_metrics": {
    "nodes": 804,
    "edges": 905,
    "communities": 354,
    "patterns_detected": 73
  },
  "risk_summary": {
    "total_entities_evaluated": 804,
    "total_entity_alerts": 0,
    "total_cluster_alerts": 1,
    "tier_counts": {
      "HIGH": 0,
      "MEDIUM": 0,
      "LOW": 804
    },
    "min_alert_tier": "MEDIUM"
  }
}
```

### `POST /api/intelligence/explain/{entity_id}`
- **Description:** Meet / AI Explanation Layer. Provides grounded, factor-based explanation based on topological properties.
- **Path Parameters:** `entity_id` (int)
- **Response (200 OK):**
```json
{
  "entity_id": 15,
  "entity_name": "Airport Police Station",
  "entity_type": "POLICE_STATION",
  "risk_score": 10.0,
  "risk_level": "LOW",
  "explanation": "Entity 'Airport Police Station' is registered as an authoritative law enforcement jurisdiction (POLICE_STATION) with 118 connected incident linkages. It serves as a jurisdictional anchor across distinct FIR filings.",
  "key_factors": [
    "Network Degree: 118 direct topological connection(s) identified",
    "High topological connectivity: acts as a multi-incident cross-FIR hub"
  ],
  "graph_metrics": {},
  "connected_entities_count": 118,
  "alerts": [],
  "confidence": 0.95
}
```

---

## 7. Alerts & Investigation Reports

### `GET /api/alerts`
- **Query Parameters:** `case_id` (int), `severity` (enum: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), `status` (enum: `OPEN`, `ACKNOWLEDGED`, `RESOLVED`)
- **Response (200 OK):** Paginated list of operational alerts.

### `PUT /api/alerts/{alert_id}/status`
- **Request Body:** `{"status": "ACKNOWLEDGED"}` or `{"status": "RESOLVED"}`
- **Response (200 OK):** Updated alert record with timestamp.

### `POST /api/reports/generate/{case_id}`
- **Description:** Generates an executive NCRB Criminal Network Investigation Report synthesizing all entities, relationships, Louvain communities, risk metrics, and alerts.
- **Response (201 Created):**
```json
{
  "id": 4,
  "case_id": 21,
  "investigation_id": null,
  "report_type": "CRIMINAL_NETWORK_SUMMARY",
  "title": "NCRB Criminal Network Intelligence Report — Case NEXUS-FIR-IMPORT-001",
  "content": "# NCRB Criminal Network Intelligence Report ...",
  "generated_by": 32,
  "created_at": "2026-09-05T19:40:00Z"
}
```

### `GET /api/reports`
- **Query Parameters:** `case_id` (optional int)
- **Response (200 OK):** List of generated reports.

---

## 8. Aayush Processing Adapter

### `GET /api/processing/aayush-handoff`
- **Description:** Exposes Aayush's processed evidence converted into the standard frozen format: `{"entities": [...], "relationships": [...], "metadata": {...}}`.

### `GET /api/processing/cross-validate`
- **Description:** Cross-validates Aayush's processed evidence against Oracle XE authoritative entities and returns alignment rate and overlap metrics.
