"""
Pydantic data models for Explainable Risk Scoring & Alerts (Phase 4).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScoringConfig(BaseModel):
    """
    Configurable scoring weights, tier boundaries, and alert filters.
    All weights are documented and adjustable without code changes.
    """
    cross_fir_weight: float = 25.0
    repeated_identifier_points: float = 25.0
    pagerank_max_points: float = 20.0
    betweenness_max_points: float = 10.0
    dense_cluster_points: float = 10.0
    unusual_structure_points: float = 10.0
    
    # Tier thresholds
    low_tier_cutoff: float = 40.0
    high_tier_cutoff: float = 70.0
    
    # Minimum tier filter for generating alerts ('LOW', 'MEDIUM', 'HIGH')
    min_alert_tier: str = "MEDIUM"


class ContributingFactor(BaseModel):
    """
    Core explainability artifact detailing the exact raw value and points contributed by a factor.
    The sum of points_contributed equals the final RiskScore.
    """
    factor_name: str
    raw_value: Any
    points_contributed: float
    description: str


class RiskScore(BaseModel):
    """
    Normalized 0-100 risk score and tier classification for an entity.
    """
    entity_id: str
    display_value: str
    entity_type: str
    score: float
    tier: str  # 'LOW' | 'MEDIUM' | 'HIGH'
    contributing_factors: List[ContributingFactor]


class ClusterAlert(BaseModel):
    """
    Aggregated alert for suspicious high-density communities.
    """
    community_id: int
    member_entity_ids: List[str]
    member_count: int
    avg_risk_score: float
    max_risk_score: float
    cluster_reasons: List[str]


class Alert(BaseModel):
    """
    Final alert payload exported to output/alerts.json.
    """
    alert_id: str
    target_id: str  # entity_id or community_id
    alert_type: str  # 'entity' | 'cluster'
    risk_score: float
    risk_tier: str  # 'LOW' | 'MEDIUM' | 'HIGH'
    reasons: List[str]
    contributing_factors: List[ContributingFactor] = Field(default_factory=list)
    source_FIR_ids: List[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
