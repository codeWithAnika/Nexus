"""
Unit tests for Nemotron-assisted LLM reason polishing and fact validation pass.
"""

import json
from unittest.mock import MagicMock
import pytest

from fir_intelligence.phase4_scoring.llm_reason_polish import polish_reasons_llm
from fir_intelligence.phase4_scoring.models import ContributingFactor, RiskScore


@pytest.fixture
def mock_llm_client():
    client = MagicMock()
    client.is_available.return_value = True
    return client


def test_polish_reasons_llm_successful(mock_llm_client):
    mock_llm_client.generate_json.return_value = {
        "polished_reasons": [
            "Ramesh Kumar appears across multiple separate FIR records.",
            "Identified as a shared phone contact linking multiple fraud suspects."
        ]
    }

    risk_score = RiskScore(
        entity_id="ENT-001",
        display_value="Ramesh Kumar",
        entity_type="Person",
        score=85.0,
        tier="HIGH",
        contributing_factors=[
            ContributingFactor(factor_name="cross_fir_appearances", raw_value=3, points_contributed=25.0, description="Appears across 3 FIRs")
        ]
    )

    templated = ["Appears across 3 separate FIRs", "Shares an identifier with other entities"]
    polished = polish_reasons_llm(risk_score, templated, mock_llm_client)

    assert len(polished) == 2
    assert "Ramesh Kumar" in polished[0] or "FIR" in polished[0]


def test_polish_reasons_llm_fallback_on_api_error(mock_llm_client):
    mock_llm_client.generate_json.side_effect = Exception("API Timeout")

    risk_score = RiskScore(
        entity_id="ENT-001",
        display_value="Ramesh Kumar",
        entity_type="Person",
        score=85.0,
        tier="HIGH",
        contributing_factors=[]
    )

    templated = ["Appears across 3 separate FIRs"]
    polished = polish_reasons_llm(risk_score, templated, mock_llm_client)

    assert polished == templated
