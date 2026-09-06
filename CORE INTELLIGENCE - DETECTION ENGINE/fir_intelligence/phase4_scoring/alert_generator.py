"""
AlertGenerator orchestrator module.
Generates explainable entity risk scores and cluster alerts, applies optional Nemotron reason polishing,
and exports output/alerts.json — the final deliverable of the intelligence engine.
"""

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fir_intelligence.phase1_extraction.entity_store import EntityStore
from fir_intelligence.phase1_extraction.llm_client import NemotronClient
from fir_intelligence.phase3_analytics.models import AnalysisResult

from .cluster_alerts import aggregate_cluster_alerts
from .llm_reason_polish import polish_reasons_llm
from .models import Alert, ClusterAlert, RiskScore, ScoringConfig
from .reason_generation import generate_reasons_from_factors
from .scoring import RiskScorer


TIER_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}


class AlertGenerator:
    """
    Orchestrates entity risk scoring, reason generation/polishing, cluster alert aggregation,
    and final export to output/alerts.json.
    """

    def __init__(self, scoring_config: Optional[ScoringConfig] = None):
        self.config = scoring_config or ScoringConfig()
        self.scorer = RiskScorer(self.config)

    def generate_alerts(
        self,
        analysis_result: AnalysisResult,
        entity_store: Optional[EntityStore] = None,
        use_llm: bool = False,
        llm_client: Optional[NemotronClient] = None,
    ) -> Dict[str, Any]:
        """
        Calculates risk scores, filters alerts based on min_alert_tier, and aggregates cluster alerts.
        """
        risk_scores_map: Dict[str, RiskScore] = {}
        entity_alerts: List[Alert] = []

        min_tier_val = TIER_ORDER.get(self.config.min_alert_tier.upper(), 2)

        # 1. Score all entities
        for ent_id, metrics in analysis_result.entity_metrics.items():
            display_val = ent_id
            ent_type = "Unknown"
            source_firs: List[str] = []

            if entity_store:
                ent = entity_store.get_entity_by_id(ent_id)
                if ent:
                    display_val = ent.display_value
                    ent_type = ent.type.value
                    source_firs = ent.source_FIR_ids

            risk_score = self.scorer.score_entity(metrics, display_value=display_val, entity_type=ent_type)
            risk_scores_map[ent_id] = risk_score

            # Check tier threshold
            if TIER_ORDER.get(risk_score.tier, 1) >= min_tier_val:
                # Primary template-based reasons
                reasons = generate_reasons_from_factors(risk_score.contributing_factors)

                # Optional Nemotron LLM reason polishing
                if use_llm and llm_client:
                    reasons = polish_reasons_llm(risk_score, reasons, llm_client)

                alert = Alert(
                    alert_id=f"ALT-ENT-{uuid.uuid4().hex[:8]}",
                    target_id=ent_id,
                    alert_type="entity",
                    risk_score=risk_score.score,
                    risk_tier=risk_score.tier,
                    reasons=reasons,
                    contributing_factors=risk_score.contributing_factors,
                    source_FIR_ids=source_firs,
                )
                entity_alerts.append(alert)

        # Sort entity alerts by risk_score descending
        entity_alerts.sort(key=lambda a: a.risk_score, reverse=True)

        # 2. Aggregate Cluster Alerts
        cluster_alerts_raw = aggregate_cluster_alerts(
            communities=analysis_result.communities,
            risk_scores_map=risk_scores_map,
            patterns=analysis_result.patterns,
        )

        cluster_alerts: List[Alert] = []
        for ca in cluster_alerts_raw:
            # Collect all FIR IDs across cluster members
            cluster_firs: List[str] = []
            if entity_store:
                for m_id in ca.member_entity_ids:
                    m_ent = entity_store.get_entity_by_id(m_id)
                    if m_ent:
                        cluster_firs.extend(m_ent.source_FIR_ids)
            cluster_firs = list(set(cluster_firs))

            cluster_tier = "HIGH" if ca.max_risk_score >= self.config.high_tier_cutoff else "MEDIUM"

            if TIER_ORDER.get(cluster_tier, 1) >= min_tier_val:
                c_alert = Alert(
                    alert_id=f"ALT-CLS-{uuid.uuid4().hex[:8]}",
                    target_id=f"COMMUNITY-{ca.community_id}",
                    alert_type="cluster",
                    risk_score=ca.max_risk_score,
                    risk_tier=cluster_tier,
                    reasons=ca.cluster_reasons,
                    source_FIR_ids=cluster_firs,
                )
                cluster_alerts.append(c_alert)

        cluster_alerts.sort(key=lambda a: a.risk_score, reverse=True)

        # 3. Assemble complete payload
        tier_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for rs in risk_scores_map.values():
            tier_counts[rs.tier] = tier_counts.get(rs.tier, 0) + 1

        payload = {
            "summary": {
                "total_entities_evaluated": len(risk_scores_map),
                "total_entity_alerts": len(entity_alerts),
                "total_cluster_alerts": len(cluster_alerts),
                "tier_counts": tier_counts,
                "min_alert_tier": self.config.min_alert_tier,
            },
            "entity_alerts": [a.model_dump() for a in entity_alerts],
            "cluster_alerts": [c.model_dump() for c in cluster_alerts],
            "all_scores": {k: v.model_dump() for k, v in risk_scores_map.items()},
        }

        return payload

    def export_json(self, alerts_payload: Dict[str, Any], filepath: Union[str, Path]) -> None:
        """Export alerts payload to JSON file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(alerts_payload, f, indent=2)
