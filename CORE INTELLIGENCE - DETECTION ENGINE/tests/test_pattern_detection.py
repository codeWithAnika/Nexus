"""
Unit tests for the 4 rule-based pattern detectors.
"""

import networkx as nx
from fir_intelligence.phase3_analytics.centrality import compute_graph_centralities
from fir_intelligence.phase3_analytics.models import CommunityData, Phase3Config
from fir_intelligence.phase3_analytics.pattern_detection import (
    detect_cross_fir_appearances,
    detect_dense_clusters,
    detect_repeated_identifiers,
    detect_unusual_structures,
)


def test_detect_repeated_identifiers():
    graph = nx.MultiDiGraph()
    graph.add_node("ENT-PH1", type="Phone", canonical_value="+919876543210")
    graph.add_node("ENT-P1", type="Person", display_value="Ramesh")
    graph.add_node("ENT-P2", type="Person", display_value="Suresh")
    graph.add_node("ENT-P3", type="Person", display_value="Mahesh")

    graph.add_edge("ENT-P1", "ENT-PH1", key="E1")
    graph.add_edge("ENT-P2", "ENT-PH1", key="E2")
    graph.add_edge("ENT-P3", "ENT-PH1", key="E3")

    config = Phase3Config(repeated_identifier_degree_threshold=2)
    matches = detect_repeated_identifiers(graph, config)

    assert len(matches) == 1
    m = matches[0]
    assert m.pattern_type == "repeated_identifier"
    assert "ENT-PH1" in m.entity_ids
    assert len(m.entity_ids) == 4
    assert m.triggering_metric_values["linked_person_count"] == 3


def test_detect_cross_fir_appearances():
    graph = nx.MultiDiGraph()
    graph.add_node("ENT-PH1", type="Phone", source_FIR_ids=["FIR-001", "FIR-002", "FIR-004"])

    config = Phase3Config(cross_fir_threshold=2)
    matches = detect_cross_fir_appearances(graph, config)

    assert len(matches) == 1
    assert matches[0].pattern_type == "cross_fir_appearance"
    assert matches[0].triggering_metric_values["fir_count"] == 3


def test_detect_dense_clusters():
    comm = CommunityData(
        community_id=1,
        size=4,
        density=0.85,
        member_entity_ids=["N1", "N2", "N3", "N4"]
    )
    config = Phase3Config(dense_cluster_density_threshold=0.40, dense_cluster_min_size=3)
    matches = detect_dense_clusters([comm], config)

    assert len(matches) == 1
    assert matches[0].pattern_type == "dense_cluster"


def test_detect_unusual_structures_star_pattern():
    graph = nx.MultiDiGraph()
    graph.add_node("CTRL", type="Person")
    for i in range(1, 6):
        leaf = f"LEAF{i}"
        graph.add_node(leaf, type="Phone")
        graph.add_edge("CTRL", leaf, key=f"E{i}")

    scores = compute_graph_centralities(graph)
    config = Phase3Config(star_pattern_degree_threshold=4, star_pattern_isolation_ratio=0.60)
    matches = detect_unusual_structures(graph, scores, config)

    assert len(matches) == 1
    assert matches[0].pattern_type == "unusual_structure"
    assert matches[0].evidence["controller_node_id"] == "CTRL"
