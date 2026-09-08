# Nexus Intelligence Engine Handoff Guide
## For: Aayushman (Core Intelligence & Detection Lead)
**Workspace Location:** `Nexus/aayushman work/SIH PS189/Aayuushman's work/fir_intelligence`

---

## 1. Production Integration Status

Your intelligence pipeline has been **fully connected** to the authoritative Oracle XE database via `app/services/intelligence_integration_service.py`.

### Exact Invocation Trace:
1. **Input:** The backend queries all 804 canonical entities and their mention provenances from Oracle XE for Case 21.
2. **Translation (`IdMapper`):** Bidirectionally maps Oracle database entity IDs to your string IDs (e.g. `ENT-45`). Maps `POLICE_STATION` to `Location` and `STATUTE` to `CaseRef` nodes.
3. **Phase 2 (`GraphBuilder`):**
   - Calls `extract_structured_field_relationships` and `extract_cooccurrence_relationships`.
   - Generates **905 relationships** across 804 entities.
4. **Phase 3 (`GraphAnalyzer`):**
   - Builds NetworkX graph: computes degree, betweenness centrality, PageRank, and Louvain community partitions (**354 communities**, **73 patterns**).
5. **Phase 4 (`RiskScorer` & `AlertGenerator`):**
   - Evaluates topological risk across all 804 entities.
   - Generates community cluster alerts for dense syndicates (e.g. `Community 92`).
6. **Persistence:** Relationships, Analyses, and Alerts are transactionally written into Oracle XE.

---

## 2. Frozen Contract Interfaces

### A. Input to Intelligence Adapter
```json
{
  "entities": [
    {
      "id": 1,
      "case_id": 21,
      "entity_type": "PERSON",
      "name": "Sumita Bera",
      "normalized_name": "Sumita Bera",
      "confidence": 0.95
    }
  ],
  "relationships": []
}
```

### B. Output Expected from Intelligence Engine
```json
{
  "risk_score": 87.0,
  "risk_level": "HIGH",
  "alerts": [
    {
      "type": "HIGH_DENSITY_CLUSTER",
      "severity": "HIGH",
      "title": "Suspicious Syndicate Cluster",
      "description": "Dense community identified with cross-jurisdictional reach."
    }
  ],
  "reasons": [
    "High betweenness centrality (broker node)",
    "Repeated occurrence across multiple FIR filings"
  ]
}
```

---

## 3. What to Work On
- Tuning community partition parameters in `phase3_analytics/community.py`.
- Refining heuristic thresholding in `phase4_scoring/scoring.py` for fine-grained risk tiering.
- Adding additional crime-specific topological pattern detectors in `phase3_analytics/pattern_detection.py`.

## 4. Grounded Factor Explanation vs LLM
The suspect reasoning endpoint (`POST /api/intelligence/explain/{entity_id}`) is strictly a **DETERMINISTIC / GROUNDED FACTOR-BASED EXPLANATION** layer. It is NOT an LLM. It derives reasons directly from mathematical graph metrics (degree, betweenness, Louvain cluster membership) and statutory violations recorded in Oracle XE.

---

## 5. What NOT to Touch
- Do **NOT** enable synthetic mock data generation in `phase1_extraction/` as authoritative. Authoritative input is strictly Oracle XE canonical entities.
- Do **NOT** introduce external LLM dependencies into the core detection path; explanations must remain grounded and admissible.
- Do **NOT** replace NetworkX or alter Oracle schema models in `backend/app/models/`.
