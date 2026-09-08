## PS26189 — Intelligence/Analysis & Risk/Detection Output (for QA)

Module: Core Intelligence / Detection Engine (Aayushman)
Status: All 4 phases complete, 43/43 tests passing as of September 2026. Stable/testable release.

### Contents
- intelligence_analysis/graph_analysis.json — per-entity centrality scores (degree, betweenness, PageRank), community assignments, and detected suspicious patterns (repeated_identifier, cross_fir_appearance, dense_cluster, unusual_structure), each with supporting evidence/metric values
- intelligence_analysis/network_graph.json — the constructed relationship graph these results are computed from
- risk_detection/alerts.json — final risk-scored entity and cluster alerts (0-100 score, LOW/MEDIUM/HIGH tier, explainable reasons, contributing factor breakdown), filtered to MEDIUM+ tier
- schemas/ — exact data model definitions (field names, types, enums) for graph_analysis.json and alerts.json, to validate structure/data-quality against
- test_results/pytest_output.txt — current full test suite result

### Known characteristics worth knowing for testing
- Risk scores are deterministic and rule-based (never LLM-generated) — re-running the pipeline on the same input should produce identical scores every time; this is a good candidate for a repeatability/determinism test
- An optional Nemotron (LLM) augmentation path exists (--use-llm flag) that affects entity/relationship extraction but NOT the scoring formula itself — if Safina wants to test that path separately, flag it as a distinct test surface since it depends on a live API key and network access, unlike the deterministic core
- Tested against synthetic sample FIR data (8 base FIRs); a larger 544-FIR real-format dataset was also run internally — ask if a larger-scale sample is needed for performance testing

Contact [Aayushman] with questions.
