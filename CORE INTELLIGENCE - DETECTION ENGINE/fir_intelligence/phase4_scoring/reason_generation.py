"""
Template-based primary reason generator.
Translates contributing factors directly into clear, human-readable bullet points matching the target output specification.
Does NOT depend on an LLM.
"""

from typing import List
from .models import ContributingFactor, RiskScore


FACTOR_REASON_TEMPLATES = {
    "cross_fir_appearances": "Appears across {raw_value} separate FIRs",
    "shared_identifier_pattern": "Shares an identifier with other entities",
    "pagerank_influence": "Connected to multiple suspicious/high-risk entities (High PageRank influence)",
    "betweenness_brokerage": "Acts as a key broker connecting distinct criminal clusters",
    "dense_cluster_membership": "Located in a high-density network cluster",
    "star_pattern_controller": "Central controller hub in an unusual star-topology network structure",
}


def generate_reasons_from_factors(factors: List[ContributingFactor]) -> List[str]:
    """
    Generates human-readable bullet points directly from contributing factors.
    """
    reasons: List[str] = []

    for factor in factors:
        template = FACTOR_REASON_TEMPLATES.get(factor.factor_name)
        if template:
            if "{raw_value}" in template:
                reasons.append(template.format(raw_value=factor.raw_value))
            else:
                reasons.append(template)
        else:
            reasons.append(factor.description)

    if not reasons:
        reasons.append("Single appearance in network with low risk indicators.")

    return list(dict.fromkeys(reasons))
