"""
Unit tests for GraphBuilder class and NetworkX MultiDiGraph construction.
"""

from pathlib import Path
import pytest
import networkx as nx

from fir_intelligence.phase1_extraction.entity_store import EntityStore
from fir_intelligence.phase1_extraction.models import Entity, EntityType
from fir_intelligence.phase2_graph.graph_builder import GraphBuilder
from fir_intelligence.phase2_graph.models import EdgeWeight, Relationship, RelationType, SourceType


def test_graph_builder(tmp_path):
    p1 = Entity(
        id="ENT-PERSON-001",
        type=EntityType.PERSON,
        canonical_value="ramesh kumar",
        display_value="Ramesh Kumar",
        source_FIR_ids=["FIR-001"],
        raw_mentions=[]
    )
    phone = Entity(
        id="ENT-PHONE-001",
        type=EntityType.PHONE,
        canonical_value="+919876543210",
        display_value="+919876543210",
        source_FIR_ids=["FIR-001"],
        raw_mentions=[]
    )

    rel = Relationship(
        id="REL-001",
        source_entity_id="ENT-PERSON-001",
        target_entity_id="ENT-PHONE-001",
        relation_type=RelationType.USES,
        source_type=SourceType.STRUCTURED_FIELD.value,
        source_FIR_ids=["FIR-001"],
        evidence="phone_numbers_mentioned",
        weight=EdgeWeight.calculate(1.0, ["FIR-001"], [SourceType.STRUCTURED_FIELD.value]),
        confidence=1.0
    )

    store = EntityStore(entities=[p1, phone])
    builder = GraphBuilder()

    graph = builder.build_from_entity_store(store, [rel])

    assert isinstance(graph, nx.MultiDiGraph)
    assert graph.number_of_nodes() == 2
    assert graph.number_of_edges() == 1

    # Check node attributes
    assert graph.nodes["ENT-PERSON-001"]["canonical_value"] == "ramesh kumar"
    assert graph.nodes["ENT-PERSON-001"]["type"] == "Person"

    # Check edge attributes
    edge_data = graph.get_edge_data("ENT-PERSON-001", "ENT-PHONE-001", "REL-001")
    assert edge_data["relation_type"] == "uses"
    assert edge_data["source_type"] == "structured_field"
    assert edge_data["weight"] > 0

    # Test exports
    graphml_path = tmp_path / "network_graph.graphml"
    json_path = tmp_path / "network_graph.json"

    builder.export_graphml(graph, graphml_path)
    builder.export_json(graph, json_path)

    assert graphml_path.exists()
    assert json_path.exists()
    assert graphml_path.stat().st_size > 0
    assert json_path.stat().st_size > 0
