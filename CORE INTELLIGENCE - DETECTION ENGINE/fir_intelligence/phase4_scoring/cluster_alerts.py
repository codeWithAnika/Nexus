"""
Suspicious Cluster Alert Aggregator module.
Aggregates member risk scores and generates cluster-level alerts for dense communities.
"""

from typing import Dict, List
from fir_intelligence.phase3_analytics.models import CommunityData, PatternMatch
from .models import ClusterAlert, RiskScore


def aggregate_cluster_alerts(
    communities: List[CommunityData],
    risk_scores_map: Dict[str, RiskScore],
    patterns: List[PatternMatch],
) -> List[ClusterAlert]:
    """
    Identifies high-risk/dense community clusters and aggregates member metrics into ClusterAlert records.
    """
    dense_community_ids = {
        p.evidence.get("community_id")
        for p in patterns
        if p.pattern_type == "dense_cluster" and p.evidence.get("community_id") is not None
    }

    alerts: List[ClusterAlert] = []

    for comm in communities:
        # Ignore isolated single-node communities
        if comm.size <= 1:
            continue

        if comm.community_id in dense_community_ids or comm.density >= 0.50:
            member_scores = [
                risk_scores_map[m].score
                for m in comm.member_entity_ids
                if m in risk_scores_map
            ]

            if not member_scores:
                continue

            avg_score = round(sum(member_scores) / float(len(member_scores)), 1)
            max_score = round(max(member_scores), 1)

            reasons = [
                f"Tightly knit community of {comm.size} entities with {comm.density:.2f} edge density",
            ]
            high_risk_members = [
                risk_scores_map[m].display_value
                for m in comm.member_entity_ids
                if m in risk_scores_map and risk_scores_map[m].tier in ("HIGH", "MEDIUM")
            ]
            if high_risk_members:
                reasons.append(f"Contains {len(high_risk_members)} elevated risk entities ({', '.join(high_risk_members[:3])})")

            alerts.append(
                ClusterAlert(
                    community_id=comm.community_id,
                    member_entity_ids=comm.member_entity_ids,
                    member_count=comm.size,
                    avg_risk_score=avg_score,
                    max_risk_score=max_score,
                    cluster_reasons=reasons,
                )
            )

    return alerts
