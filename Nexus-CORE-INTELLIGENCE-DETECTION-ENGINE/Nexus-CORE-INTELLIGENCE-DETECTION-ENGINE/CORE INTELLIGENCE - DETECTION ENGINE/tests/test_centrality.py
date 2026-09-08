"""
Unit tests for centrality metrics computation.
"""

import networkx as nx
from fir_intelligence.phase3_analytics.centrality import compute_graph_centralities


def test_compute_graph_centralities():
    graph = nx.MultiDiGraph()
    graph.add_node("ENT-P1", type="Person", display_value="Ramesh")
    graph.add_node("ENT-P2", type="Person", display_value="Suresh")
    graph.add_node("ENT-PH1", type="Phone", display_value="+919876543210")

    graph.add_edge("ENT-P1", "ENT-PH1", key="E1", weight=1.0)
    graph.add_edge("ENT-P2", "ENT-PH1", key="E2", weight=1.0)

    scores = compute_graph_centralities(graph)

    assert len(scores) == 3
    ph1_scores = scores["ENT-PH1"]
    assert ph1_scores.in_degree == 2
    assert ph1_scores.total_degree == 2
    assert ph1_scores.pagerank > 0
    assert ph1_scores.betweenness_centrality >= 0
