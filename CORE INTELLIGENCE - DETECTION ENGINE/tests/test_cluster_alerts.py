"""
Unit tests for cluster alert aggregation.
"""

from fir_intelligence.phase3_analytics.models import CommunityData, PatternMatch
from fir_intelligence.phase4_scoring.cluster_alerts import aggregate_cluster_alerts
from fir_intelligence.phase4_scoring.models import ContributingFactor, RiskScore


def test_aggregate_cluster_alerts():
    comm = CommunityData(
        community_id=1,
        size=3,
        density=0.67,
        member_entity_ids=["ENT-P1", "ENT-PH1", "ENT-LOC1"]
    )

    risk_map = {
        "ENT-P1": RiskScore(entity_id="ENT-P1", display_value="Ramesh", entity_type="Person", score=85.0, tier="HIGH", contributing_factors=[]),
        "ENT-PH1": RiskScore(entity_id="ENT-PH1", display_value="+919876543210", entity_type="Phone", score=75.0, tier="HIGH", contributing_factors=[]),
        "ENT-LOC1": RiskScore(entity_id="ENT-LOC1", display_value="Dwarka", entity_type="Location", score=30.0, tier="LOW", contributing_factors=[]),
    }

    patterns = [
        PatternMatch(
            pattern_id="PAT-DENSE-1",
            pattern_type="dense_cluster",
            entity_ids=["ENT-P1", "ENT-PH1", "ENT-LOC1"],
            evidence={"community_id": 1},
            triggering_metric_values={"density": 0.67}
        )
    ]

    cluster_alerts = aggregate_cluster_alerts([comm], risk_map, patterns)

    assert len(cluster_alerts) == 1
    ca = cluster_alerts[0]
    assert ca.community_id == 1
    assert ca.member_count == 3
    assert ca.avg_risk_score == round((85 + 75 + 30) / 3.0, 1)
    assert ca.max_risk_score == 85.0
    assert len(ca.cluster_reasons) >= 1
