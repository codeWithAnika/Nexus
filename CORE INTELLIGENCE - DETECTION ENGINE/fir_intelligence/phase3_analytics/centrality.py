"""
Centrality metrics computation module.
Computes in-degree, out-degree, total degree, degree centrality, betweenness centrality,
and weighted PageRank for nodes in a NetworkX MultiDiGraph.
"""

from typing import Dict
import networkx as nx
from .models import CentralityScores


def collapse_multigraph_to_weighted_simple(graph: nx.MultiDiGraph) -> nx.Graph:
    """
    Collapses a MultiDiGraph into a weighted simple undirected graph.
    Summing edge weights between node pairs ensures stable, normalized calculations
    for Betweenness Centrality and PageRank without multi-edge inflation.
    """
    simple_g = nx.Graph()

    for node, data in graph.nodes(data=True):
        simple_g.add_node(node, **data)

    for u, v, k, data in graph.edges(data=True, keys=True):
        weight = data.get("weight", 1.0)
        if simple_g.has_edge(u, v):
            simple_g[u][v]["weight"] += weight
        else:
            simple_g.add_edge(u, v, weight=weight)

    return simple_g


def compute_graph_centralities(graph: nx.MultiDiGraph) -> Dict[str, CentralityScores]:
    """
    Computes degree metrics directly on the MultiDiGraph and normalized betweenness & PageRank
    on the collapsed weighted simple graph.
    """
    if graph.number_of_nodes() == 0:
        return {}

    # 1. Degree metrics from MultiDiGraph
    in_degrees = dict(graph.in_degree())
    out_degrees = dict(graph.out_degree())
    total_degrees = dict(graph.degree())
    nx_deg_centrality = nx.degree_centrality(graph)

    # 2. Collapse to simple weighted graph for Betweenness and PageRank
    simple_g = collapse_multigraph_to_weighted_simple(graph)

    try:
        betweenness = nx.betweenness_centrality(simple_g, weight="weight")
    except Exception:
        betweenness = {n: 0.0 for n in graph.nodes()}

    try:
        pr = nx.pagerank(simple_g, weight="weight")
    except Exception:
        pr = {n: round(1.0 / max(1, graph.number_of_nodes()), 6) for n in graph.nodes()}

    scores: Dict[str, CentralityScores] = {}
    for n in graph.nodes():
        scores[n] = CentralityScores(
            in_degree=in_degrees.get(n, 0),
            out_degree=out_degrees.get(n, 0),
            total_degree=total_degrees.get(n, 0),
            degree_centrality=round(nx_deg_centrality.get(n, 0.0), 4),
            betweenness_centrality=round(betweenness.get(n, 0.0), 4),
            pagerank=round(pr.get(n, 0.0), 6),
        )

    return scores
