"""
GraphAnalyzer class for orchestrating Phase 3 Graph Analytics and Pattern Detection.
Exposes clean AnalysisResult interface consumed by Phase 4 (Risk Scoring & Alerts).
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import networkx as nx

from .centrality import compute_graph_centralities
from .community import detect_louvain_communities
from .models import (
    AnalysisResult,
    CentralityScores,
    CommunityData,
    EntityMetrics,
    PatternMatch,
    Phase3Config,
)
from .pattern_detection import (
    detect_cross_fir_appearances,
    detect_dense_clusters,
    detect_repeated_identifiers,
    detect_unusual_structures,
)


class GraphAnalyzer:
    """
    Orchestrates centrality calculation, Louvain community detection, and suspicious pattern detection
    over a NetworkX MultiDiGraph.
    """

    def __init__(self, config: Optional[Phase3Config] = None):
        self.config = config or Phase3Config()

    def compute_centrality_metrics(self, graph: nx.MultiDiGraph) -> Dict[str, CentralityScores]:
        """Compute degree, betweenness, and PageRank centralities."""
        return compute_graph_centralities(graph)

    def detect_communities(
        self, graph: nx.MultiDiGraph
    ) -> Tuple[Dict[str, int], List[CommunityData]]:
        """Detect Louvain communities and compute density metrics."""
        return detect_louvain_communities(graph)

    def detect_patterns(
        self,
        graph: nx.MultiDiGraph,
        centrality_scores: Dict[str, CentralityScores],
        communities: List[CommunityData],
    ) -> List[PatternMatch]:
        """Execute all 4 rule-based pattern detectors."""
        patterns: List[PatternMatch] = []
        patterns.extend(detect_repeated_identifiers(graph, self.config))
        patterns.extend(detect_cross_fir_appearances(graph, self.config))
        patterns.extend(detect_dense_clusters(communities, self.config))
        patterns.extend(detect_unusual_structures(graph, centrality_scores, self.config))
        return patterns

    def run_full_analysis(self, graph: nx.MultiDiGraph) -> AnalysisResult:
        """
        Runs complete analytics workflow and packages results into an AnalysisResult model.
        """
        # 1. Compute centralities
        centrality_map = self.compute_centrality_metrics(graph)

        # 2. Detect communities
        node_comm_map, community_list = self.detect_communities(graph)

        # 3. Detect patterns
        pattern_list = self.detect_patterns(graph, centrality_map, community_list)

        # Map pattern flags per entity
        entity_pattern_flags: Dict[str, List[str]] = {}
        for p in pattern_list:
            for ent_id in p.entity_ids:
                if ent_id in graph:
                    entity_pattern_flags.setdefault(ent_id, []).append(p.pattern_type)

        # 4. Assemble per-entity metrics
        entity_metrics: Dict[str, EntityMetrics] = {}
        for node, data in graph.nodes(data=True):
            fir_ids = data.get("source_FIR_ids", [])
            if isinstance(fir_ids, str):
                fir_ids = [f.strip() for f in fir_ids.split(",") if f.strip()]
            cross_fir_count = len(set(fir_ids))

            scores = centrality_map.get(
                node,
                CentralityScores(
                    in_degree=0, out_degree=0, total_degree=0,
                    degree_centrality=0.0, betweenness_centrality=0.0, pagerank=0.0
                ),
            )
            comm_id = node_comm_map.get(node, 0)
            flags = list(set(entity_pattern_flags.get(node, [])))

            entity_metrics[node] = EntityMetrics(
                entity_id=node,
                centrality=scores,
                community_id=comm_id,
                cross_fir_count=cross_fir_count,
                pattern_flags=flags,
            )

        # 5. Build summary
        pattern_counts: Dict[str, int] = {}
        for p in pattern_list:
            pattern_counts[p.pattern_type] = pattern_counts.get(p.pattern_type, 0) + 1

        summary = {
            "num_nodes": graph.number_of_nodes(),
            "num_edges": graph.number_of_edges(),
            "num_communities": len(community_list),
            "num_pattern_matches": len(pattern_list),
            "pattern_counts": pattern_counts,
        }

        return AnalysisResult(
            entity_metrics=entity_metrics,
            communities=community_list,
            patterns=pattern_list,
            summary=summary,
        )

    def export_json(self, analysis_result: AnalysisResult, filepath: Union[str, Path]) -> None:
        """Export AnalysisResult to JSON file for Phase 4 consumption."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(analysis_result.model_dump(), f, indent=2)
