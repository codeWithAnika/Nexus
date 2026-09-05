"""Nexus Entity Resolution Pilot Package.

Deterministic, conservative entity resolution and provenance persistence pilot.
"""
from app.entity_resolution.models import (
    CandidateResolution,
    PilotResolutionReport,
    ResolutionDecision,
)
from app.entity_resolution.resolver import ConservativeEntityResolver
from app.entity_resolution.service import (
    resolve_and_persist_pilot,
    resolve_and_persist_validation_batch,
)

__all__ = [
    "CandidateResolution",
    "ConservativeEntityResolver",
    "PilotResolutionReport",
    "ResolutionDecision",
    "resolve_and_persist_pilot",
    "resolve_and_persist_validation_batch",
]
