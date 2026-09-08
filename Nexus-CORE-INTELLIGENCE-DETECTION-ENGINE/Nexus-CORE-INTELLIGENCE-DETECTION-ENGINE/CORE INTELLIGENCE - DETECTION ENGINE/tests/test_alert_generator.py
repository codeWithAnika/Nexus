"""
Integration tests for AlertGenerator class and output/alerts.json export.
"""

from pathlib import Path
import pytest

from fir_intelligence.phase1_extraction.entity_store import EntityStore
from fir_intelligence.phase1_extraction.extractors import extract_all_mentions
from fir_intelligence.phase1_extraction.ingestion import load_firs_from_json
from fir_intelligence.phase1_extraction.resolution import EntityResolver
from fir_intelligence.phase2_graph.graph_builder import GraphBuilder
from fir_intelligence.phase2_graph.relationship_rules import (
    extract_cooccurrence_relationships,
    extract_structured_field_relationships,
)
from fir_intelligence.phase3_analytics.analyzer import GraphAnalyzer
from fir_intelligence.phase3_analytics.models import Phase3Config
from fir_intelligence.phase4_scoring.alert_generator import AlertGenerator
from fir_intelligence.phase4_scoring.models import ScoringConfig


FIXTURES_PATH = Path(__file__).parent / "fixtures" / "sample_firs.json"


def test_alert_generator_end_to_end(tmp_path):
    # 1. Phase 1
    firs = load_firs_from_json(FIXTURES_PATH)
    all_mentions = [m for fir in firs for m in extract_all_mentions(fir)]
    resolver = EntityResolver()
    entities, candidate_merges, merge_history = resolver.resolve_mentions(all_mentions)
    store = EntityStore(entities=entities)

    # 2. Phase 2
    s_rels = extract_structured_field_relationships(store)
    c_rels = extract_cooccurrence_relationships(store)
    builder = GraphBuilder()
    graph = builder.build_from_entity_store(store, s_rels + c_rels)

    # 3. Phase 3
    analyzer = GraphAnalyzer(Phase3Config())
    analysis_result = analyzer.run_full_analysis(graph)

    # 4. Phase 4
    alert_gen = AlertGenerator(ScoringConfig(min_alert_tier="MEDIUM"))
    alerts_payload = alert_gen.generate_alerts(analysis_result, entity_store=store)

    assert "entity_alerts" in alerts_payload
    assert "cluster_alerts" in alerts_payload
    assert len(alerts_payload["entity_alerts"]) > 0

    # Check top alert has HIGH or MEDIUM tier
    top_alert = alerts_payload["entity_alerts"][0]
    assert top_alert["risk_tier"] in ("HIGH", "MEDIUM")
    assert top_alert["risk_score"] >= 40.0
    assert len(top_alert["reasons"]) > 0
    assert len(top_alert["contributing_factors"]) > 0

    # Test export
    out_alerts_json = tmp_path / "alerts.json"
    alert_gen.export_json(alerts_payload, out_alerts_json)

    assert out_alerts_json.exists()
    assert out_alerts_json.stat().st_size > 0
