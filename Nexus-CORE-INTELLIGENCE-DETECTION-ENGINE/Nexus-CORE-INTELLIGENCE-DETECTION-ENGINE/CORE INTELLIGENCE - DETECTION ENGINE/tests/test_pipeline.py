"""
End-to-end integration test running Phase 1 pipeline on sample FIR fixtures.
"""

from pathlib import Path
import pytest

from fir_intelligence.phase1_extraction.entity_store import EntityStore
from fir_intelligence.phase1_extraction.extractors import extract_all_mentions
from fir_intelligence.phase1_extraction.ingestion import load_firs_from_json
from fir_intelligence.phase1_extraction.resolution import EntityResolver


FIXTURES_PATH = Path(__file__).parent / "fixtures" / "sample_firs.json"


def test_full_pipeline_on_sample_firs(tmp_path):
    # 1. Ingestion
    firs = load_firs_from_json(FIXTURES_PATH)
    assert len(firs) == 12
    assert firs[0].case_ref == "FIR-2023-DEL-001"

    # 2. Mention Extraction across all FIRs
    all_mentions = []
    for fir in firs:
        mentions = extract_all_mentions(fir)
        all_mentions.extend(mentions)

    assert len(all_mentions) > 20
    # Verify every mention has source FIR ID traceability
    for m in all_mentions:
        assert m.source_FIR_id is not None
        assert m.source_FIR_id != ""

    # 3. Normalization & Resolution
    resolver = EntityResolver(fuzzy_merge_threshold=0.82, candidate_merge_threshold=0.70)
    entities, candidate_merges, merge_history = resolver.resolve_mentions(all_mentions)

    # 4. EntityStore Interface Verification
    store = EntityStore(
        entities=entities,
        candidate_merges=candidate_merges,
        merge_history=merge_history
    )

    all_entities = store.get_all_entities()
    assert len(all_entities) > 0

    # Cross-FIR entity check: Phone number +919876543210 should appear across multiple FIRs
    phone_entities = store.get_entities_by_type("Phone")
    target_phone = [p for p in phone_entities if p.canonical_value == "+919876543210"]
    assert len(target_phone) == 1
    assert len(target_phone[0].source_FIR_ids) >= 3

    # 5. Phase 2, 3, 4 Pipeline Execution Assertions
    from fir_intelligence.phase2_graph.graph_builder import GraphBuilder
    from fir_intelligence.phase2_graph.relationship_rules import extract_cooccurrence_relationships, extract_structured_field_relationships
    from fir_intelligence.phase3_analytics.analyzer import GraphAnalyzer
    from fir_intelligence.phase3_analytics.models import Phase3Config
    from fir_intelligence.phase4_scoring.alert_generator import AlertGenerator
    from fir_intelligence.phase4_scoring.models import ScoringConfig

    s_rels = extract_structured_field_relationships(store)
    c_rels = extract_cooccurrence_relationships(store)
    builder = GraphBuilder()
    nx_graph = builder.build_from_entity_store(store, s_rels + c_rels)

    analyzer = GraphAnalyzer(Phase3Config())
    analysis_result = analyzer.run_full_analysis(nx_graph)
    assert len(analysis_result.patterns) > 0

    alert_gen = AlertGenerator(ScoringConfig(min_alert_tier="MEDIUM"))
    alerts_payload = alert_gen.generate_alerts(analysis_result, entity_store=store)

    # Verify at least one HIGH tier entity alert exists
    high_alerts = [a for a in alerts_payload["entity_alerts"] if a["risk_tier"] == "HIGH"]
    assert len(high_alerts) >= 1
    assert high_alerts[0]["risk_score"] >= 70.0

    # Export test
    json_out = tmp_path / "entities_output.json"
    csv_out = tmp_path / "entities_output.csv"

    store.export_json(json_out)
    store.export_csv(csv_out)

    assert json_out.exists()
    assert csv_out.exists()
    assert json_out.stat().st_size > 0
    assert csv_out.stat().st_size > 0
