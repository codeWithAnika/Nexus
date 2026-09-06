## PS26189 — Intelligence Engine Output Handoff (for Backend/DB)

These are the real output shapes from the Core Intelligence Engine (Phases 1-4), meant to inform the DB schema and API layer.

### Output → Table mapping
| Output file | Maps to your table(s) |
|---|---|
| deduplicated_entities.json | ENTITIES, ENTITY_IDENTIFIERS |
| network_graph.json / .graphml | RELATIONSHIPS |
| graph_analysis.json | ANALYSIS_RESULTS |
| alerts.json | RISK_SCORES, ALERTS |

### Two schema points to align on before finalizing tables

1. **source_fir_id (singular) vs. source_FIR_ids (list):**
   A single relationship in this engine can be supported by evidence from MULTIPLE FIRs (this is part of the edge-weighting logic — see EdgeWeight.fir_support_count in phase2_models.py). Your current RELATIONSHIPS schema assumes one FK per relationship. Options: (a) add a join table (e.g. RELATIONSHIP_SOURCE_FIRS) to hold a many-to-many mapping, or (b) flatten multi-FIR relationships into multiple rows on ingest. Needs a decision before implementation.

2. **evidence_id vs. evidence (text):**
   The engine currently produces `evidence` as a plain text string/snippet on each relationship (see the `evidence` field in phase2_models.py's Relationship model), not a foreign key into a stored EVIDENCE record. If your EVIDENCE table expects a proper ID referencing a stored document, we need to decide whether: (a) the engine should be updated to emit an evidence_id alongside the snippet, or (b) your ingestion layer creates the EVIDENCE row and generates the ID at insert time from the snippet text.

### File guide
- sample_outputs/ — real JSON output from a full pipeline run on 8 synthetic sample FIRs (plus a larger 544-FIR real dataset was also tested internally, not included here — ask if you need that sample too)
- schemas/ — the exact pydantic model definitions each output file is serialized from; use these as the source of truth for field names/types rather than inferring from the JSON alone

Contact [Aayushman] with questions before finalizing the schema, especially on the two points above.
