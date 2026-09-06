"""
Community detection module.
Performs Louvain community detection using NetworkX and calculates community size and edge density.
"""

from typing import Dict, List, Tuple
import networkx as nx
from .centrality import collapse_multigraph_to_weighted_simple
from .models import CommunityData


def detect_louvain_communities(
    graph: nx.MultiDiGraph,
) -> Tuple[Dict[str, int], List[CommunityData]]:
    """
    Performs Louvain community detection on collapsed weighted graph.
    Returns (node_to_community_map, list_of_community_data).
    """
    if graph.number_of_nodes() == 0:
        return {}, []

    simple_g = collapse_multigraph_to_weighted_simple(graph)

    try:
        communities_sets = nx.community.louvain_communities(simple_g, weight="weight", seed=42)
    except Exception:
        # Fallback to connected components if Louvain fails
        communities_sets = list(nx.connected_components(simple_g))

    node_to_community: Dict[str, int] = {}
    community_data_list: List[CommunityData] = []

    for comm_id, member_set in enumerate(communities_sets, start=1):
        members = list(member_set)
        for m in members:
            node_to_community[m] = comm_id

        size = len(members)
        if size <= 1:
            density = 1.0
        else:
            subgraph = simple_g.subgraph(members)
            actual_edges = subgraph.number_of_edges()
            possible_edges = (size * (size - 1)) / 2.0
            density = round(actual_edges / possible_edges, 4)

        community_data_list.append(
            CommunityData(
                community_id=comm_id,
                size=size,
                density=density,
                member_entity_ids=members,
            )
        )

    return node_to_community, community_data_list
