"""
Pydantic data models for Graph Analytics & Pattern Detection (Phase 3).
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Phase3Config(BaseModel):
    """
    Configurable detection thresholds for structural analysis and pattern detection.
    Eliminates magic numbers for flexible tuning against production data.
    """
    repeated_identifier_degree_threshold: int = 2
    cross_fir_threshold: int = 2
    dense_cluster_density_threshold: float = 0.40
    dense_cluster_min_size: int = 3
    star_pattern_degree_threshold: int = 4
    star_pattern_isolation_ratio: float = 0.60


class CentralityScores(BaseModel):
    """
    Structural centrality metrics per entity node.
    """
    in_degree: int
    out_degree: int
    total_degree: int
    degree_centrality: float
    betweenness_centrality: float
    pagerank: float


class CommunityData(BaseModel):
    """
    Louvain community metric summary.
    """
    community_id: int
    size: int
    density: float
    member_entity_ids: List[str]


class PatternMatch(BaseModel):
    """
    Structured record representing a detected suspicious pattern.
    Provides complete evidence and metric values for explainability in Phase 4 scoring.
    """
    pattern_id: str
    pattern_type: str  # 'repeated_identifier' | 'cross_fir_appearance' | 'dense_cluster' | 'unusual_structure'
    entity_ids: List[str]
    evidence: Dict[str, Any]
    triggering_metric_values: Dict[str, Any]


class EntityMetrics(BaseModel):
    """
    Aggregated metric vector per entity node.
    """
    entity_id: str
    centrality: CentralityScores
    community_id: int
    cross_fir_count: int
    pattern_flags: List[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    """
    Bundled output contract from Phase 3 consumed directly by Phase 4 (Risk Scoring & Alerts).
    """
    entity_metrics: Dict[str, EntityMetrics]
    communities: List[CommunityData]
    patterns: List[PatternMatch]
    summary: Dict[str, Any]
