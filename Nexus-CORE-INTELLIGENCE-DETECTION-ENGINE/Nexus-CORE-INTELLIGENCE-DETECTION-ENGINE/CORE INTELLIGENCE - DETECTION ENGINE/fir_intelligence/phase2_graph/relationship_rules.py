"""
Deterministic relationship extraction rules.
Extracts structured-field and co-occurrence relationships from resolved EntityStore.
Each rule function is independently testable.
"""

import uuid
from typing import Dict, List, Set, Tuple
from fir_intelligence.phase1_extraction.entity_store import EntityStore
from fir_intelligence.phase1_extraction.models import Entity, EntityType
from .models import EdgeWeight, Relationship, RelationType, SourceType


def extract_structured_field_relationships(entity_store: EntityStore) -> List[Relationship]:
    """
    Extracts high-confidence relationships derived directly from structured FIR fields.
    e.g. Person --visited--> Location, Person --uses--> Phone, Person --transaction--> Transaction.
    """
    entities = entity_store.get_all_entities()
    relationships: List[Relationship] = []

    # Map FIR IDs to entities present in that FIR by entity type
    fir_map: Dict[str, Dict[EntityType, List[Entity]]] = {}
    for ent in entities:
        for fir_id in ent.source_FIR_ids:
            fir_map.setdefault(fir_id, {}).setdefault(ent.type, []).append(ent)

    seen_rel_keys: Set[Tuple[str, str, str, str]] = set()

    for fir_id, type_dict in fir_map.items():
        persons = type_dict.get(EntityType.PERSON, [])
        locations = type_dict.get(EntityType.LOCATION, [])
        phones = type_dict.get(EntityType.PHONE, [])
        accounts = type_dict.get(EntityType.ACCOUNT, [])
        transactions = type_dict.get(EntityType.TRANSACTION, [])

        # 1. Person --visited--> Location (from structured address fields)
        for person in persons:
            for loc in locations:
                rel_key = (person.id, loc.id, RelationType.VISITED.value, fir_id)
                if rel_key not in seen_rel_keys:
                    seen_rel_keys.add(rel_key)
                    
                    # Determine evidence field
                    p_fields = [m.field_source for m in person.raw_mentions if m.source_FIR_id == fir_id]
                    l_fields = [m.field_source for m in loc.raw_mentions if m.source_FIR_id == fir_id]
                    evidence = f"structured_fields: {','.join(p_fields)} & {','.join(l_fields)}"

                    weight = EdgeWeight.calculate(
                        base_weight=1.0,
                        fir_ids=[fir_id],
                        source_types=[SourceType.STRUCTURED_FIELD.value],
                        conf1=person.confidence,
                        conf2=loc.confidence,
                    )

                    relationships.append(
                        Relationship(
                            id=f"REL-{uuid.uuid4().hex[:8]}",
                            source_entity_id=person.id,
                            target_entity_id=loc.id,
                            relation_type=RelationType.VISITED,
                            source_type=SourceType.STRUCTURED_FIELD.value,
                            source_FIR_ids=[fir_id],
                            evidence=evidence,
                            weight=weight,
                            confidence=1.0,
                        )
                    )

        # 2. Person --uses--> Phone (from phone_numbers_mentioned)
        for person in persons:
            for phone in phones:
                rel_key = (person.id, phone.id, RelationType.USES.value, fir_id)
                if rel_key not in seen_rel_keys:
                    seen_rel_keys.add(rel_key)
                    evidence = f"structured_field: phone_numbers_mentioned in {fir_id}"
                    
                    weight = EdgeWeight.calculate(
                        base_weight=1.0,
                        fir_ids=[fir_id],
                        source_types=[SourceType.STRUCTURED_FIELD.value],
                        conf1=person.confidence,
                        conf2=phone.confidence,
                    )

                    relationships.append(
                        Relationship(
                            id=f"REL-{uuid.uuid4().hex[:8]}",
                            source_entity_id=person.id,
                            target_entity_id=phone.id,
                            relation_type=RelationType.USES,
                            source_type=SourceType.STRUCTURED_FIELD.value,
                            source_FIR_ids=[fir_id],
                            evidence=evidence,
                            weight=weight,
                            confidence=1.0,
                        )
                    )

        # 3. Person --owns--> Account
        for person in persons:
            for acc in accounts:
                rel_key = (person.id, acc.id, RelationType.OWNS.value, fir_id)
                if rel_key not in seen_rel_keys:
                    seen_rel_keys.add(rel_key)
                    evidence = f"structured_field: account in {fir_id}"

                    weight = EdgeWeight.calculate(
                        base_weight=1.0,
                        fir_ids=[fir_id],
                        source_types=[SourceType.STRUCTURED_FIELD.value],
                        conf1=person.confidence,
                        conf2=acc.confidence,
                    )

                    relationships.append(
                        Relationship(
                            id=f"REL-{uuid.uuid4().hex[:8]}",
                            source_entity_id=person.id,
                            target_entity_id=acc.id,
                            relation_type=RelationType.OWNS,
                            source_type=SourceType.STRUCTURED_FIELD.value,
                            source_FIR_ids=[fir_id],
                            evidence=evidence,
                            weight=weight,
                            confidence=1.0,
                        )
                    )

        # 4. Person --transaction--> Transaction
        for person in persons:
            for tx in transactions:
                rel_key = (person.id, tx.id, RelationType.TRANSACTION.value, fir_id)
                if rel_key not in seen_rel_keys:
                    seen_rel_keys.add(rel_key)
                    evidence = f"structured_field: amounts_mentioned in {fir_id}"

                    weight = EdgeWeight.calculate(
                        base_weight=1.0,
                        fir_ids=[fir_id],
                        source_types=[SourceType.STRUCTURED_FIELD.value],
                        conf1=person.confidence,
                        conf2=tx.confidence,
                    )

                    relationships.append(
                        Relationship(
                            id=f"REL-{uuid.uuid4().hex[:8]}",
                            source_entity_id=person.id,
                            target_entity_id=tx.id,
                            relation_type=RelationType.TRANSACTION,
                            source_type=SourceType.STRUCTURED_FIELD.value,
                            source_FIR_ids=[fir_id],
                            evidence=evidence,
                            weight=weight,
                            confidence=1.0,
                        )
                    )

    return relationships


def extract_cooccurrence_relationships(entity_store: EntityStore) -> List[Relationship]:
    """
    Extracts co-occurrence relationships when entities appear in the same source FIR.
    e.g. Person --connected_to--> Person, Person --associated_with--> Organization.
    """
    entities = entity_store.get_all_entities()
    relationships: List[Relationship] = []

    # Map FIR IDs to entities
    fir_map: Dict[str, List[Entity]] = {}
    for ent in entities:
        for fir_id in ent.source_FIR_ids:
            fir_map.setdefault(fir_id, []).append(ent)

    seen_pairs: Set[Tuple[str, str, str]] = set()

    for fir_id, fir_entities in fir_map.items():
        # Pairwise co-occurrence
        for i in range(len(fir_entities)):
            for j in range(i + 1, len(fir_entities)):
                ent1 = fir_entities[i]
                ent2 = fir_entities[j]

                # Ensure canonical pair ordering for undirected co-occurrence tracking
                pair_key = (min(ent1.id, ent2.id), max(ent1.id, ent2.id), fir_id)
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                # Determine relationship type
                rel_type = None
                if ent1.type == EntityType.PERSON and ent2.type == EntityType.PERSON:
                    rel_type = RelationType.CONNECTED_TO
                elif ent1.type == EntityType.PERSON and ent2.type in (EntityType.ORGANIZATION, EntityType.LOCATION, EntityType.DEVICE):
                    rel_type = RelationType.ASSOCIATED_WITH
                elif ent2.type == EntityType.PERSON and ent1.type in (EntityType.ORGANIZATION, EntityType.LOCATION, EntityType.DEVICE):
                    rel_type = RelationType.ASSOCIATED_WITH
                    # Swap so Person is source
                    ent1, ent2 = ent2, ent1

                if rel_type is not None:
                    evidence = f"co_occurrence in source FIR {fir_id}"
                    weight = EdgeWeight.calculate(
                        base_weight=0.50,
                        fir_ids=[fir_id],
                        source_types=[SourceType.CO_OCCURRENCE.value],
                        conf1=ent1.confidence,
                        conf2=ent2.confidence,
                    )

                    relationships.append(
                        Relationship(
                            id=f"REL-{uuid.uuid4().hex[:8]}",
                            source_entity_id=ent1.id,
                            target_entity_id=ent2.id,
                            relation_type=rel_type,
                            source_type=SourceType.CO_OCCURRENCE.value,
                            source_FIR_ids=[fir_id],
                            evidence=evidence,
                            weight=weight,
                            confidence=0.80,
                        )
                    )

    return relationships
