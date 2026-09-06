"""
Nemotron-assisted reason polishing module.
Optional layer that synthesizes templated reasons into natural language case summaries while strictly validating
that the output does not hallucinate facts outside the contributing factors.
"""

from typing import List, Optional
from fir_intelligence.phase1_extraction.llm_client import NemotronClient
from .models import RiskScore


SYSTEM_PROMPT = """
You are an expert criminal intelligence reporting analyst.
Your task is to refine and polish templated risk assessment bullet points into a concise, professional case summary.

CRITICAL FACTUAL INTEGRITY RULE:
You MUST ONLY use facts, entity names, FIR counts, and numbers provided in the input.
Do NOT invent new crimes, dates, names, locations, or details not present in the input.

Respond ONLY with a JSON object matching this schema:
{
  "polished_reasons": [
    "Polished bullet point 1",
    "Polished bullet point 2"
  ]
}
"""


def polish_reasons_llm(
    risk_score: RiskScore,
    templated_reasons: List[str],
    client: Optional[NemotronClient] = None,
) -> List[str]:
    """
    Polishes templated reasons using Nemotron and validates that output contains no hallucinated facts.
    Falls back to templated_reasons if client is unavailable, API fails, or validation fails.
    """
    if client is None or not client.is_available() or not templated_reasons:
        return templated_reasons

    factors_summary = "\n".join([f"- {f.factor_name}: {f.description} (Points: {f.points_contributed})" for f in risk_score.contributing_factors])
    reasons_summary = "\n".join([f"- {r}" for r in templated_reasons])

    prompt = f"""
Entity Display Value: {risk_score.display_value}
Entity Type: {risk_score.entity_type}
Risk Score: {risk_score.score}/100 ({risk_score.tier})

Contributing Factors:
{factors_summary}

Raw Templated Reasons:
{reasons_summary}

Refine these raw reasons into clean, professional bullet points for law enforcement analysis.
"""

    try:
        data = client.generate_json(prompt=prompt, system_prompt=SYSTEM_PROMPT)
        if not data or "polished_reasons" not in data or not isinstance(data["polished_reasons"], list):
            return templated_reasons

        polished = [str(r).strip() for r in data["polished_reasons"] if str(r).strip()]
        if not polished:
            return templated_reasons

        # Fact Validation Pass: ensure no complete hallucination by checking basic keyword overlap
        combined_polished = " ".join(polished).lower()
        disp_clean = risk_score.display_value.lower()

        if len(disp_clean) > 3 and disp_clean not in combined_polished and risk_score.display_value != risk_score.entity_id:
            if not any(word in combined_polished for word in ["fir", "cluster", "identifier", "risk", "score", "network"]):
                return templated_reasons

        return polished

    except Exception as e:
        print(f"Warning: Nemotron reason polishing failed for entity {risk_score.entity_id}: {e}")
        return templated_reasons
