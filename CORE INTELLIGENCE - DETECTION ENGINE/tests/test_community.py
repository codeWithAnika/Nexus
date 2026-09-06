"""
Unit tests for Louvain community detection.
"""

import networkx as nx
from fir_intelligence.phase3_analytics.community import detect_louvain_communities


def test_detect_louvain_communities():
    graph = nx.MultiDiGraph()
    # Clique 1
    for i in range(1, 4):
        graph.add_node(f"N{i}", type="Person")
    graph.add_edge("N1", "N2", key="E1", weight=1.0)
    graph.add_edge("N2", "N3", key="E2", weight=1.0)
    graph.add_edge("N3", "N1", key="E3", weight=1.0)

    # Clique 2
    for i in range(4, 7):
        graph.add_node(f"N{i}", type="Person")
    graph.add_edge("N4", "N5", key="E4", weight=1.0)
    graph.add_edge("N5", "N6", key="E5", weight=1.0)
    graph.add_edge("N6", "N4", key="E6", weight=1.0)

    # Connecting edge
    graph.add_edge("N3", "N4", key="E7", weight=0.5)

    node_map, comm_list = detect_louvain_communities(graph)

    assert len(node_map) == 6
    assert len(comm_list) >= 1
    for comm in comm_list:
        assert comm.size > 0
        assert 0.0 <= comm.density <= 1.0
