"""
Unit tests for primary template-based reason generator.
"""

from fir_intelligence.phase4_scoring.models import ContributingFactor
from fir_intelligence.phase4_scoring.reason_generation import generate_reasons_from_factors


def test_generate_reasons_from_factors():
    factors = [
        ContributingFactor(factor_name="cross_fir_appearances", raw_value=3, points_contributed=25.0, description="Appears across 3 separate FIRs"),
        ContributingFactor(factor_name="shared_identifier_pattern", raw_value=True, points_contributed=25.0, description="Shared identifier"),
        ContributingFactor(factor_name="dense_cluster_membership", raw_value=1, points_contributed=10.0, description="Dense cluster"),
    ]

    reasons = generate_reasons_from_factors(factors)

    assert len(reasons) == 3
    assert any("3 separate FIRs" in r for r in reasons)
    assert any("Shares an identifier" in r for r in reasons)
    assert any("high-density network cluster" in r for r in reasons)
