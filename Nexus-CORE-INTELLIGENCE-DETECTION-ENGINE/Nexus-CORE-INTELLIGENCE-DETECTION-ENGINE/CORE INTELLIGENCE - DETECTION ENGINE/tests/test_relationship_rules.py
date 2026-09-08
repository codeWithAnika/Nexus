"""
Unit tests for deterministic relationship extraction rules.
"""

from fir_intelligence.phase1_extraction.entity_store import EntityStore
from fir_intelligence.phase1_extraction.models import Entity, EntityType, RawMention
from fir_intelligence.phase2_graph.models import RelationType, SourceType
from fir_intelligence.phase2_graph.relationship_rules import (
    extract_cooccurrence_relationships,
    extract_structured_field_relationships,
)


def test_extract_structured_field_relationships():
    # Setup test entities
    person = Entity(
        id="ENT-PERSON-001",
        type=EntityType.PERSON,
        canonical_value="ramesh kumar",
        display_value="Ramesh Kumar",
        source_FIR_ids=["FIR-001"],
        raw_mentions=[RawMention(entity_type=EntityType.PERSON, raw_value="Ramesh Kumar", source_FIR_id="FIR-001", field_source="accused_name")]
    )
    phone = Entity(
        id="ENT-PHONE-001",
        type=EntityType.PHONE,
        canonical_value="+919876543210",
        display_value="+919876543210",
        source_FIR_ids=["FIR-001"],
        raw_mentions=[RawMention(entity_type=EntityType.PHONE, raw_value="9876543210", source_FIR_id="FIR-001", field_source="phone_numbers_mentioned")]
    )
    location = Entity(
        id="ENT-LOC-001",
        type=EntityType.LOCATION,
        canonical_value="dwarka sector 4",
        display_value="Dwarka Sector 4",
        source_FIR_ids=["FIR-001"],
        raw_mentions=[RawMention(entity_type=EntityType.LOCATION, raw_value="Dwarka Sector 4", source_FIR_id="FIR-001", field_source="accused_address")]
    )

    store = EntityStore(entities=[person, phone, location])
    rels = extract_structured_field_relationships(store)

    assert len(rels) >= 2
    rel_types = {r.relation_type for r in rels}
    assert RelationType.USES in rel_types
    assert RelationType.VISITED in rel_types

    for r in rels:
        assert r.source_type == SourceType.STRUCTURED_FIELD.value
        assert "FIR-001" in r.source_FIR_ids
        assert r.weight.computed_weight > 0


def test_extract_cooccurrence_relationships():
    p1 = Entity(
        id="ENT-PERSON-001",
        type=EntityType.PERSON,
        canonical_value="ramesh kumar",
        display_value="Ramesh Kumar",
        source_FIR_ids=["FIR-003"],
        raw_mentions=[]
    )
    p2 = Entity(
        id="ENT-PERSON-002",
        type=EntityType.PERSON,
        canonical_value="amitabh singh",
        display_value="Amitabh Singh",
        source_FIR_ids=["FIR-003"],
        raw_mentions=[]
    )

    store = EntityStore(entities=[p1, p2])
    rels = extract_cooccurrence_relationships(store)

    assert len(rels) == 1
    rel = rels[0]
    assert rel.relation_type == RelationType.CONNECTED_TO
    assert rel.source_type == SourceType.CO_OCCURRENCE.value
    assert "FIR-003" in rel.source_FIR_ids
