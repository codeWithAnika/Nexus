"""
Unit tests for LLM narrative relationship extraction using mocked NemotronClient responses.
"""

import json
from unittest.mock import MagicMock
import pytest

from fir_intelligence.phase1_extraction.entity_store import EntityStore
from fir_intelligence.phase1_extraction.models import Entity, EntityType, RawFIR
from fir_intelligence.phase2_graph.llm_relationship_extractor import extract_llm_relationships
from fir_intelligence.phase2_graph.models import RelationType, SourceType


@pytest.fixture
def mock_store_and_firs():
    e1 = Entity(id="ENT-P1", type=EntityType.PERSON, canonical_value="ramesh kumar", display_value="Ramesh Kumar", source_FIR_ids=["FIR-001"], raw_mentions=[])
    e2 = Entity(id="ENT-PH1", type=EntityType.PHONE, canonical_value="+919876543210", display_value="+919876543210", source_FIR_ids=["FIR-001"], raw_mentions=[])
    store = EntityStore(entities=[e1, e2])

    fir = RawFIR(fir_id="FIR-001", case_ref="FIR-001", incident_narrative="Ramesh Kumar uses phone +919876543210.")
    return store, [fir]


def test_extract_llm_relationships(mock_store_and_firs):
    store, firs = mock_store_and_firs

    mock_client = MagicMock()
    mock_client.is_available.return_value = True
    mock_client.generate_json.return_value = {
        "relationships": [
            {
                "source_text": "Ramesh Kumar",
                "target_text": "+919876543210",
                "relation_type": "uses",
                "evidence": "Ramesh Kumar uses phone +919876543210",
            }
        ]
    }

    rels = extract_llm_relationships(firs, store, mock_client)

    assert len(rels) == 1
    rel = rels[0]
    assert rel.source_entity_id == "ENT-P1"
    assert rel.target_entity_id == "ENT-PH1"
    assert rel.relation_type == RelationType.USES
    assert rel.source_type == SourceType.LLM_INFERRED
