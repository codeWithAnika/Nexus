# PS26189 — AI-Powered Criminal Network Analysis System
## Complete Pipeline: Phases 1 to 4 (FIR Extraction → Alerts)

This repository contains the complete 4-phase intelligence engine for **PS26189: AI-Powered Criminal Network Analysis System**.

The pipeline ingests raw or structured First Information Reports (FIRs), extracts and resolves entities, mines relationships, constructs a weighted multi-directed network graph, computes graph analytics and pattern matches, and outputs 100% explainable risk scores and alerts.

---

### Complete Pipeline Architecture

```
                 +---------------------------------------+
                 |  Structured / Raw FIR Input Data      |
                 |  (JSON arrays / CSV records)          |
                 +-------------------+-------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
| Phase 1: FIR Extraction & Entity Resolution Engine                       |
|  - Structured & Regex Extractors (Phones, Emails, Dates, Amounts)       |
|  - Nemotron LLM Free-Text Narrative NER                                 |
|  - Entity Normalization (Honorifics, Address Abbreviation Expansion)    |
|  - Hybrid Resolution (Exact Match + RapidFuzz + Contextual Boosting)    |
|  - EntityStore Contract & Source FIR Traceability                       |
+------------------------------------+------------------------------------+
                                     | Consumes EntityStore
                                     v
+-------------------------------------------------------------------------+
| Phase 2: Relationship Mining & Graph Construction Engine                |
|  - Structured Field Rules (Person --owns--> Account, Person --uses--> Phone) |
|  - Co-occurrence Rules (Person --connected_to--> Person in same FIR)    |
|  - Nemotron Narrative Relationship Inference (JSON Triples)             |
|  - Transparent Edge Weighting Calculation                               |
|  - NetworkX MultiDiGraph Construction & Exporters (GraphML, JSON)       |
+------------------------------------+------------------------------------+
                                     | Consumes NetworkX MultiDiGraph
                                     v
+-------------------------------------------------------------------------+
| Phase 3: Graph Analytics & Pattern Detection Engine                     |
|  - Centralities: In/Out/Total Degree, Betweenness, PageRank             |
|  - Louvain Community Detection & Density Metrics                        |
|  - 4 Explainable Rule-Based Pattern Detectors:                          |
|      1. repeated_identifier   2. cross_fir_appearance                   |
|      3. dense_cluster         4. unusual_structure (Star Pattern)       |
|  - AnalysisResult Contract for Phase 4                                  |
+------------------------------------+------------------------------------+
                                     | Consumes AnalysisResult
                                     v
+-------------------------------------------------------------------------+
| Phase 4: Explainable Risk Scoring & Alert Generation Engine             |
|  - Deterministic 0-100 Risk Scorer (Sum of ContributingFactors)         |
|  - Risk Tier Classification (LOW: 0-39 | MEDIUM: 40-69 | HIGH: 70-100)    |
|  - Template-Based Primary Reason Generator                              |
|  - Nemotron LLM Optional Reason Polishing & Fact Validation Pass        |
|  - Suspicious Cluster Alert Aggregation                                 |
|  - Export to output/alerts.json (Final Deliverable)                     |
+-------------------------------------------------------------------------+
```

---

### Worked Example: An Entity's Journey (Raw FIR -> Final Alert)

Below is a step-by-step trace showing how **Ramesh Kumar Sharma** is processed across all 4 phases:

#### 1. Input (Raw FIRs):
- **FIR-2023-DEL-001**: Accused `"Ramesh Kumar"`, Phone `"+91 9876543210"`, Address `"Plot No 12, Sec 4, Dwarka, Delhi"`.
- **FIR-2023-DEL-002**: Accused `"Ramesh Kumar Sharma"`, Phone `"9876543210"`, Address `"Plot 12, Sector 4, Dwarka, New Delhi"`.
- **FIR-2023-BLR-004**: Accused `"R. K. Sharma"`, Phone `"+91 9876543210"`, Address `"Sec 4 Dwarka New Delhi"`.

#### 2. Phase 1: Normalization & Resolution:
- Normalizer strips honorifics -> Canonical: `"ramesh kumar sharma"`, Display: `"Ramesh Kumar Sharma"`.
- Shared Phone `+919876543210` across FIRs triggers **Contextual Boosting** (+0.15 boost).
- Fuzzy similarity (RapidFuzz + Context Boost = 0.88 >= 0.82 threshold) auto-merges all 3 mentions into single Entity **`ENT-PERSON-02dcdbb4`**.
- Audit log entry created in `MergeDecision` with reasoning `fuzzy_score:0.88 (token_sort_ratio:0.88; shared_identifier:phone|+919876543210)`.

#### 3. Phase 2: Relationship Mining & Graph Construction:
- Direct edge created: `Ramesh Kumar Sharma --uses--> +919876543210` (`source_type: structured_field`, `weight: 1.0`).
- Co-occurrence edge created: `Ramesh Kumar Sharma --connected_to--> Smt. Sunita Sharma` (`source_type: co_occurrence`, `weight: 0.5`).
- MultiDiGraph constructed with 48 nodes and 83 edges.

#### 4. Phase 3: Graph Analytics & Pattern Detection:
- Centrality computed: PageRank = `0.0582`, Betweenness = `0.0158`.
- Assigned to Louvain Community **#12**.
- Pattern 1 matched: **`repeated_identifier`** (linked via shared phone `+919876543210` to 5 distinct person entities).
- Pattern 2 matched: **`cross_fir_appearance`** (appears across 3 separate FIRs).

#### 5. Phase 4: Risk Scoring & Alert Output:
- Deterministic scoring calculation:
  - `cross_fir_appearances` (3 FIRs): **+12.5 pts**
  - `shared_identifier_pattern`: **+25.0 pts**
  - `pagerank_influence` (0.0582): **+11.6 pts**
  - `betweenness_brokerage` (0.0158): **+1.6 pts**
  - **Final Score**: **50.7 / 100** -> Tier: **`MEDIUM`**
- Exported Alert in `output/alerts.json`:
```json
{
  "alert_id": "ALT-ENT-a1b2c3d4",
  "target_id": "ENT-PERSON-02dcdbb4",
  "alert_type": "entity",
  "risk_score": 50.7,
  "risk_tier": "MEDIUM",
  "reasons": [
    "Appears across 3 separate FIRs",
    "Shares an identifier with other entities",
    "Connected to multiple suspicious/high-risk entities (High PageRank influence)",
    "Acts as a key broker connecting distinct criminal clusters"
  ],
  "contributing_factors": [
    {"factor_name": "cross_fir_appearances", "raw_value": 3, "points_contributed": 12.5, "description": "Appears across 3 separate FIRs"},
    {"factor_name": "shared_identifier_pattern", "raw_value": true, "points_contributed": 25.0, "description": "Shared identifier linked to multiple distinct person entities"},
    {"factor_name": "pagerank_influence", "raw_value": 0.0582, "points_contributed": 11.6, "description": "High network PageRank influence score (0.0582)"},
    {"factor_name": "betweenness_brokerage", "raw_value": 0.0158, "points_contributed": 1.6, "description": "Acts as a key network broker between clusters (Betweenness 0.0158)"}
  ],
  "source_FIR_ids": ["FIR-2023-DEL-001", "FIR-2023-DEL-002", "FIR-2023-BLR-004"]
}
```

---

### Project Directory Structure

```
c:\PROJECTS\SIH PS189\Aayuushman's work\
├── fir_intelligence/
│   ├── __init__.py
│   ├── phase1_extraction/             # Phase 1: Extraction & Entity Resolution
│   │   ├── __init__.py
│   │   ├── models.py                  # RawFIR, Entity, RawMention, MergeDecision
│   │   ├── ingestion.py               # JSON/CSV loaders
│   │   ├── extractors.py              # Regex extractors
│   │   ├── normalizers.py             # Canonicalization functions
│   │   ├── resolution.py              # Hybrid entity resolution
│   │   ├── entity_store.py            # EntityStore output interface
│   │   ├── llm_client.py              # Nemotron NIM API wrapper
│   │   ├── llm_extractors.py          # Narrative NER via Nemotron
│   │   └── llm_merge_reasoner.py      # Ambiguous merge reasoning
│   ├── phase2_graph/                  # Phase 2: Relationship Mining & Graph Construction
│   │   ├── __init__.py
│   │   ├── models.py                  # Relationship, EdgeWeight, RelationType
│   │   ├── relationship_rules.py      # Deterministic extraction rules
│   │   ├── llm_relationship_extractor.py # Nemotron narrative relationship inference
│   │   ├── graph_builder.py           # NetworkX MultiDiGraph builder & exporter
│   │   └── visualization.py          # Debug & analytics graph rendering
│   ├── phase3_analytics/              # Phase 3: Graph Analytics & Pattern Detection
│   │   ├── __init__.py
│   │   ├── models.py                  # Phase3Config, CentralityScores, CommunityData, PatternMatch, EntityMetrics, AnalysisResult
│   │   ├── centrality.py              # Degree, Betweenness, PageRank computations
│   │   ├── community.py               # Louvain community detection & metrics
│   │   ├── pattern_detection.py       # 4 Rule-based pattern detectors
│   │   └── analyzer.py                # GraphAnalyzer orchestrator class
│   └── phase4_scoring/                # Phase 4: Explainable Risk Scoring & Alerts
│       ├── __init__.py
│       ├── models.py                  # ScoringConfig, RiskScore, ContributingFactor, ClusterAlert, Alert
│       ├── scoring.py                 # RiskScorer class & deterministic scoring formula
│       ├── reason_generation.py        # Primary template-based reason generator
│       ├── llm_reason_polish.py         # Nemotron-assisted reason polishing & fact validation
│       ├── cluster_alerts.py             # ClusterAlert aggregation logic
│       └── alert_generator.py             # AlertGenerator class & final orchestration
├── tests/
│   ├── __init__.py
│   ├── test_extractors.py
│   ├── test_normalizers.py
│   ├── test_resolution.py
│   ├── test_pipeline.py
│   ├── test_llm_client.py
│   ├── test_relationship_rules.py
│   ├── test_llm_relationship_extractor.py
│   ├── test_graph_builder.py
│   ├── test_centrality.py
│   ├── test_community.py
│   ├── test_pattern_detection.py
│   ├── test_analyzer.py
│   ├── test_scoring.py               # Phase 4 RiskScorer unit tests
│   ├── test_reason_generation.py      # Phase 4 Reason generator unit tests
│   ├── test_llm_reason_polish.py     # Phase 4 Mocked LLM reason polish tests
│   ├── test_cluster_alerts.py        # Phase 4 Cluster alert unit tests
│   ├── test_alert_generator.py       # Phase 4 AlertGenerator integration tests
│   └── fixtures/
│       ├── sample_firs.json           # 8 synthetic FIR records
│       ├── sample_relationships.json  # Expected relationship fixtures
│       ├── expected_analysis.json     # Expected analytics fixture
│       └── expected_alerts.json       # Expected alerts fixture
├── run_pipeline.py                    # CLI script executing full Phase 1-4 pipeline
└── README.md
```

---

### Execution Guide

#### 1. Full Pipeline Execution (Deterministic Baseline)
Execute all 4 phases end-to-end:
```bash
python run_pipeline.py
```

#### 2. Full Pipeline Execution with Nemotron LLM Augmentation
Set your NVIDIA API Key and run:
```bash
$env:NVIDIA_API_KEY="nvapi-..."
python run_pipeline.py --use-llm
```

#### 3. Running Unit and Integration Tests
Execute the full pytest test suite (all 43 tests pass cleanly):
```bash
pytest -v
```

---

### Exported Output Artifacts (`output/`)

Upon completion, the pipeline exports all key intelligence artifacts:
- `output/deduplicated_entities.json` & `entities_summary.csv` (Phase 1 Entities)
- `output/network_graph.json` & `network_graph.graphml` (Phase 2 Network Graph)
- `output/network_graph.png` & `network_graph.html` (Phase 2 Graph Visualizations)
- `output/graph_analysis.json` & `network_graph_analytics.png` (Phase 3 Analytics)
- `output/alerts.json` (Phase 4 Final Intelligence Alerts)
