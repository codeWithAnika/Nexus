"""
Rule-based pattern detection engine.
Identifies explainable suspicious criminal network structures:
1. Repeated Identifier (Shared Phone/Email/Account/Device across multiple Persons)
2. Cross-FIR Appearance (Entity appearing across multiple FIRs)
3. Dense Cluster (Tightly knit community with high internal edge density)
4. Unusual Structure (Star pattern: central controller node connected to isolated leaf nodes)
"""

import uuid
from typing import Dict, List
import networkx as nx

from .models import CentralityScores, CommunityData, PatternMatch, Phase3Config


IDENTIFIER_TYPES = {"Phone", "Email", "Account", "Device", "IP"}


def detect_repeated_identifiers(
    graph: nx.MultiDiGraph,
    config: Phase3Config,
) -> List[PatternMatch]:
    """
    Flags identifier entities (Phone, Email, Account, Device, IP) connected to multiple distinct Person nodes.
    """
    matches: List[PatternMatch] = []

    for node, data in graph.nodes(data=True):
        ent_type = data.get("type", "")
        if ent_type in IDENTIFIER_TYPES:
            # Find neighbors of type Person
            neighbors = set(graph.predecessors(node)).union(set(graph.successors(node)))
            linked_persons = [
                nbr for nbr in neighbors
                if graph.nodes[nbr].get("type") == "Person"
            ]

            if len(linked_persons) >= config.repeated_identifier_degree_threshold:
                person_names = [graph.nodes[p].get("display_value", p) for p in linked_persons]
                fir_ids = data.get("source_FIR_ids", [])
                
                match = PatternMatch(
                    pattern_id=f"PAT-REP-ID-{uuid.uuid4().hex[:8]}",
                    pattern_type="repeated_identifier",
                    entity_ids=[node] + linked_persons,
                    evidence={
                        "identifier_id": node,
                        "identifier_type": ent_type,
                        "canonical_value": data.get("canonical_value", ""),
                        "linked_person_ids": linked_persons,
                        "linked_person_names": person_names,
                        "source_FIR_ids": fir_ids,
                    },
                    triggering_metric_values={
                        "linked_person_count": len(linked_persons),
                        "degree_threshold": config.repeated_identifier_degree_threshold,
                    },
                )
                matches.append(match)

    return matches


def detect_cross_fir_appearances(
    graph: nx.MultiDiGraph,
    config: Phase3Config,
) -> List[PatternMatch]:
    """
    Flags entities appearing across multiple separate FIRs.
    """
    matches: List[PatternMatch] = []

    for node, data in graph.nodes(data=True):
        fir_ids = data.get("source_FIR_ids", [])
        if isinstance(fir_ids, str):
            fir_ids = [f.strip() for f in fir_ids.split(",") if f.strip()]

        unique_firs = list(dict.fromkeys(fir_ids))
        if len(unique_firs) >= config.cross_fir_threshold:
            match = PatternMatch(
                pattern_id=f"PAT-XFIR-{uuid.uuid4().hex[:8]}",
                pattern_type="cross_fir_appearance",
                entity_ids=[node],
                evidence={
                    "entity_id": node,
                    "entity_type": data.get("type", ""),
                    "display_value": data.get("display_value", ""),
                    "source_FIR_ids": unique_firs,
                },
                triggering_metric_values={
                    "fir_count": len(unique_firs),
                    "cross_fir_threshold": config.cross_fir_threshold,
                },
            )
            matches.append(match)

    return matches


def detect_dense_clusters(
    communities: List[CommunityData],
    config: Phase3Config,
) -> List[PatternMatch]:
    """
    Flags communities with density above threshold AND size above minimum.
    """
    matches: List[PatternMatch] = []

    for comm in communities:
        if (
            comm.size >= config.dense_cluster_min_size
            and comm.density >= config.dense_cluster_density_threshold
        ):
            match = PatternMatch(
                pattern_id=f"PAT-DENSE-{uuid.uuid4().hex[:8]}",
                pattern_type="dense_cluster",
                entity_ids=comm.member_entity_ids,
                evidence={
                    "community_id": comm.community_id,
                    "size": comm.size,
                    "density": comm.density,
                    "member_count": len(comm.member_entity_ids),
                },
                triggering_metric_values={
                    "density": comm.density,
                    "density_threshold": config.dense_cluster_density_threshold,
                    "size": comm.size,
                    "min_size_threshold": config.dense_cluster_min_size,
                },
            )
            matches.append(match)

    return matches


def detect_unusual_structures(
    graph: nx.MultiDiGraph,
    centrality_scores: Dict[str, CentralityScores],
    config: Phase3Config,
) -> List[PatternMatch]:
    """
    Flags star patterns: one central controller node with high degree connected mostly
    to isolated/low-degree leaf nodes.
    """
    matches: List[PatternMatch] = []

    for node, scores in centrality_scores.items():
        if scores.total_degree >= config.star_pattern_degree_threshold:
            neighbors = set(graph.predecessors(node)).union(set(graph.successors(node)))
            if not neighbors:
                continue

            isolated_count = sum(
                1 for nbr in neighbors
                if centrality_scores.get(nbr, CentralityScores(in_degree=0, out_degree=0, total_degree=0, degree_centrality=0, betweenness_centrality=0, pagerank=0)).total_degree <= 2
            )
            ratio = isolated_count / float(len(neighbors))

            if ratio >= config.star_pattern_isolation_ratio:
                node_data = graph.nodes[node]
                match = PatternMatch(
                    pattern_id=f"PAT-STAR-{uuid.uuid4().hex[:8]}",
                    pattern_type="unusual_structure",
                    entity_ids=[node] + list(neighbors),
                    evidence={
                        "controller_node_id": node,
                        "controller_display_value": node_data.get("display_value", node),
                        "controller_type": node_data.get("type", ""),
                        "total_neighbors": len(neighbors),
                        "isolated_neighbors_count": isolated_count,
                        "isolation_ratio": round(ratio, 2),
                    },
                    triggering_metric_values={
                        "degree": scores.total_degree,
                        "degree_threshold": config.star_pattern_degree_threshold,
                        "isolation_ratio": round(ratio, 2),
                        "isolation_ratio_threshold": config.star_pattern_isolation_ratio,
                    },
                )
                matches.append(match)

    return matches
