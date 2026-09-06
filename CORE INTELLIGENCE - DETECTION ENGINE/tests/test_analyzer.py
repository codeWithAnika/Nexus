"""
Integration tests for GraphAnalyzer class and AnalysisResult export.
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
from fir_intelligence.phase3_analytics.models import AnalysisResult, Phase3Config


FIXTURES_PATH = Path(__file__).parent / "fixtures" / "sample_firs.json"


def test_graph_analyzer_integration(tmp_path):
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
    result = analyzer.run_full_analysis(graph)

    assert isinstance(result, AnalysisResult)
    assert len(result.entity_metrics) == graph.number_of_nodes()
    assert len(result.communities) > 0
    assert len(result.patterns) > 0

    # Verify at least cross_fir_appearance and repeated_identifier patterns triggered on sample dataset
    p_types = {p.pattern_type for p in result.patterns}
    assert "cross_fir_appearance" in p_types or "repeated_identifier" in p_types

    # Test export
    out_json = tmp_path / "graph_analysis.json"
    analyzer.export_json(result, out_json)

    assert out_json.exists()
    assert out_json.stat().st_size > 0
