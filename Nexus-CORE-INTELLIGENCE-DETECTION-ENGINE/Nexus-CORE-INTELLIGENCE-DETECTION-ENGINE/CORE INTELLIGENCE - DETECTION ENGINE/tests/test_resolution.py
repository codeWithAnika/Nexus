"""
Unit tests for entity resolution (deduplication, fuzzy matching, contextual boosting, audit log).
"""

from fir_intelligence.phase1_extraction.models import EntityType, RawMention
from fir_intelligence.phase1_extraction.resolution import EntityResolver


def test_exact_match_merge():
    mentions = [
        RawMention(
            entity_type=EntityType.PHONE,
            raw_value="9876543210",
            source_FIR_id="FIR-001",
            field_source="phone_numbers_mentioned"
        ),
        RawMention(
            entity_type=EntityType.PHONE,
            raw_value="+91 98765 43210",
            source_FIR_id="FIR-002",
            field_source="narrative_text"
        )
    ]
    resolver = EntityResolver()
    entities, candidates, decisions = resolver.resolve_mentions(mentions)

    assert len(entities) == 1
    phone_ent = entities[0]
    assert phone_ent.canonical_value == "+919876543210"
    assert set(phone_ent.source_FIR_ids) == {"FIR-001", "FIR-002"}
    assert len(decisions) >= 1
    assert "exact_match" in decisions[0].reasoning


def test_fuzzy_match_merge_and_explainability():
    mentions = [
        RawMention(
            entity_type=EntityType.PERSON,
            raw_value="Ramesh Kumar",
            source_FIR_id="FIR-001",
            field_source="accused_name"
        ),
        RawMention(
            entity_type=EntityType.PERSON,
            raw_value="Ramesh Kumar Sharma",
            source_FIR_id="FIR-002",
            field_source="accused_name"
        )
    ]
    resolver = EntityResolver(fuzzy_merge_threshold=0.75)
    entities, candidates, decisions = resolver.resolve_mentions(mentions)

    assert len(entities) == 1
    person = entities[0]
    assert "FIR-001" in person.source_FIR_ids
    assert "FIR-002" in person.source_FIR_ids
    assert len(person.merge_history) >= 1
    assert "token_sort_ratio" in person.merge_history[0].reasoning


def test_contextual_boosting_with_shared_phone():
    # Two slightly different name spellings across FIRs that share a phone number
    mentions = [
        RawMention(
            entity_type=EntityType.PERSON,
            raw_value="R. K. Sharma",
            source_FIR_id="FIR-004",
            field_source="accused_name"
        ),
        RawMention(
            entity_type=EntityType.PERSON,
            raw_value="Ramesh Sharma",
            source_FIR_id="FIR-006",
            field_source="accused_name"
        ),
        # Shared phone across FIR-004 and FIR-006
        RawMention(
            entity_type=EntityType.PHONE,
            raw_value="9876543210",
            source_FIR_id="FIR-004",
            field_source="phone_numbers_mentioned"
        ),
        RawMention(
            entity_type=EntityType.PHONE,
            raw_value="9876543210",
            source_FIR_id="FIR-006",
            field_source="phone_numbers_mentioned"
        ),
    ]

    resolver = EntityResolver(fuzzy_merge_threshold=0.80)
    entities, candidates, decisions = resolver.resolve_mentions(mentions)

    person_entities = [e for e in entities if e.type == EntityType.PERSON]
    assert len(person_entities) == 1
    merged_person = person_entities[0]
    assert set(merged_person.source_FIR_ids) == {"FIR-004", "FIR-006"}
    
    # Verify contextual boost reasoning is logged
    reasoning = merged_person.merge_history[0].reasoning
    assert "shared_identifier:phone" in reasoning or "shared_fir" in reasoning


def test_candidate_merge_flagging():
    # Ambioguous names that fall in candidate merge range (e.g. 0.70 <= score < 0.85)
    mentions = [
        RawMention(
            entity_type=EntityType.PERSON,
            raw_value="Siddharth Mukherjee",
            source_FIR_id="FIR-007",
            field_source="accused_name"
        ),
        RawMention(
            entity_type=EntityType.PERSON,
            raw_value="Siddharth Banerjee",
            source_FIR_id="FIR-009",
            field_source="accused_name"
        )
    ]
    # Set high auto-merge threshold so these are flagged as candidate merges
    resolver = EntityResolver(fuzzy_merge_threshold=0.90, candidate_merge_threshold=0.60)
    entities, candidates, decisions = resolver.resolve_mentions(mentions)

    # Should NOT auto merge
    person_entities = [e for e in entities if e.type == EntityType.PERSON]
    assert len(person_entities) == 2
    assert len(candidates) >= 1
    assert candidates[0].entity_type == EntityType.PERSON
