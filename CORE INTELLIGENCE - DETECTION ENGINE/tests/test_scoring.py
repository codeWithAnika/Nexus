"""
Unit tests for deterministic RiskScorer.
"""

import pytest
from fir_intelligence.phase3_analytics.models import CentralityScores, EntityMetrics
from fir_intelligence.phase4_scoring.models import ScoringConfig
from fir_intelligence.phase4_scoring.scoring import RiskScorer


def test_risk_scorer_high_tier_hub():
    metrics = EntityMetrics(
        entity_id="ENT-HIGH-001",
        centrality=CentralityScores(
            in_degree=5, out_degree=2, total_degree=7,
            degree_centrality=0.15, betweenness_centrality=0.20, pagerank=0.08
        ),
        community_id=1,
        cross_fir_count=3,
        pattern_flags=["repeated_identifier", "cross_fir_appearance", "dense_cluster", "unusual_structure"]
    )

    scorer = RiskScorer(ScoringConfig())
    risk_score = scorer.score_entity(metrics, display_value="Ramesh Kumar (Suspect)")

    assert risk_score.score >= 70.0
    assert risk_score.tier == "HIGH"
    
    # Verify contributing factors sum to score
    total_pts = sum(f.points_contributed for f in risk_score.contributing_factors)
    assert abs(total_pts - risk_score.score) < 0.2
    assert len(risk_score.contributing_factors) >= 4


def test_risk_scorer_low_tier_entity():
    metrics = EntityMetrics(
        entity_id="ENT-LOW-001",
        centrality=CentralityScores(
            in_degree=1, out_degree=0, total_degree=1,
            degree_centrality=0.01, betweenness_centrality=0.0, pagerank=0.005
        ),
        community_id=2,
        cross_fir_count=1,
        pattern_flags=[]
    )

    scorer = RiskScorer(ScoringConfig())
    risk_score = scorer.score_entity(metrics, display_value="Plain Location")

    assert risk_score.score < 40.0
    assert risk_score.tier == "LOW"
