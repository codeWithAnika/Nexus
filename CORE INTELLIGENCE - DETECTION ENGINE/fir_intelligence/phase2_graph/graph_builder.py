"""
GraphBuilder class for constructing NetworkX MultiDiGraph from resolved entities and relationships.
Provides GraphML and JSON export capabilities for downstream Phase 3 analytics.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Union
import networkx as nx

from fir_intelligence.phase1_extraction.entity_store import EntityStore
from .models import Relationship


class GraphBuilder:
    """
    Constructs a NetworkX MultiDiGraph from EntityStore entities and extracted Relationship objects.
    Preserves node attributes, edge relation types, weights, evidence, and provenance.
    """

    def __init__(self):
        pass

    def build_from_entity_store(
        self,
        entity_store: EntityStore,
        relationships: List[Relationship],
    ) -> nx.MultiDiGraph:
        """
        Populates a NetworkX MultiDiGraph with entities as nodes and relationships as edges.
        """
        graph = nx.MultiDiGraph()

        # 1. Add all resolved entities as nodes
        for ent in entity_store.get_all_entities():
            graph.add_node(
                ent.id,
                id=ent.id,
                type=ent.type.value,
                canonical_value=ent.canonical_value,
                display_value=ent.display_value,
                source_FIR_ids=ent.source_FIR_ids,
                confidence=ent.confidence,
                raw_mentions_count=len(ent.raw_mentions),
            )

        # 2. Add relationships as multi-directed edges
        for rel in relationships:
            # Ensure source and target nodes exist (or create placeholder if missing)
            if not graph.has_node(rel.source_entity_id):
                graph.add_node(rel.source_entity_id, id=rel.source_entity_id, type="Unknown")
            if not graph.has_node(rel.target_entity_id):
                graph.add_node(rel.target_entity_id, id=rel.target_entity_id, type="Unknown")

            graph.add_edge(
                rel.source_entity_id,
                rel.target_entity_id,
                key=rel.id,
                id=rel.id,
                relation_type=rel.relation_type.value,
                source_type=rel.source_type,
                source_FIR_ids=rel.source_FIR_ids,
                evidence=rel.evidence,
                weight=rel.weight.computed_weight,
                weight_components=rel.weight.model_dump(),
                confidence=rel.confidence,
            )

        return graph

    def export_graphml(self, graph: nx.MultiDiGraph, filepath: Union[str, Path]) -> None:
        """
        Exports graph to standard GraphML format for Neo4j / Gephi import.
        Converts list attributes (like source_FIR_ids) to string representations for GraphML compatibility.
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        g_copy = graph.copy()
        for _, data in g_copy.nodes(data=True):
            if "source_FIR_ids" in data and isinstance(data["source_FIR_ids"], list):
                data["source_FIR_ids"] = ",".join(data["source_FIR_ids"])

        for _, _, _, data in g_copy.edges(data=True, keys=True):
            if "source_FIR_ids" in data and isinstance(data["source_FIR_ids"], list):
                data["source_FIR_ids"] = ",".join(data["source_FIR_ids"])
            if "weight_components" in data and isinstance(data["weight_components"], dict):
                data["weight_components"] = json.dumps(data["weight_components"])

        nx.write_graphml(g_copy, str(path))

    def export_json(self, graph: nx.MultiDiGraph, filepath: Union[str, Path]) -> None:
        """
        Exports graph to structured JSON format consumed by Phase 3 (Graph Analytics).
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        nodes_data = []
        for n, data in graph.nodes(data=True):
            nodes_data.append(dict(data))

        edges_data = []
        for u, v, k, data in graph.edges(data=True, keys=True):
            edge_dict = dict(data)
            edge_dict["source"] = u
            edge_dict["target"] = v
            edges_data.append(edge_dict)

        export_data = {
            "summary": {
                "num_nodes": graph.number_of_nodes(),
                "num_edges": graph.number_of_edges(),
                "is_directed": graph.is_directed(),
                "is_multigraph": graph.is_multigraph(),
            },
            "nodes": nodes_data,
            "edges": edges_data,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2)
