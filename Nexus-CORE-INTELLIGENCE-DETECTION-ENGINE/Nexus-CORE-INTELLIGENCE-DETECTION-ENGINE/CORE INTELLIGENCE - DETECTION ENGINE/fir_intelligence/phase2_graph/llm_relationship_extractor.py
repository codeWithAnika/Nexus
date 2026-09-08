"""
Narrative Relationship Inference module using Nemotron LLM.
Infers relationships between resolved entities in FIR narratives and links them to EntityStore IDs.
"""

from typing import List, Optional
from rapidfuzz.distance import JaroWinkler

from fir_intelligence.phase1_extraction.entity_store import EntityStore
from fir_intelligence.phase1_extraction.llm_client import NemotronClient
from fir_intelligence.phase1_extraction.models import RawFIR
from .models import EdgeWeight, Relationship, RelationType, SourceType


SYSTEM_PROMPT = """
You are an expert Criminal Intelligence Relationship Mining Assistant.
Analyze the incident narrative and extract explicit relationships between entities.

Allowed relation_type values:
- "owns"
- "uses"
- "visited"
- "transaction"
- "connected_to"
- "associated_with"

Respond ONLY with a JSON object matching this schema:
{
  "relationships": [
    {
      "source_text": "Entity Name A",
      "target_text": "Entity Name B",
      "relation_type": "owns|uses|visited|transaction|connected_to|associated_with",
      "evidence": "Supporting quote from narrative"
    }
  ]
}
"""


def _find_matching_entity_id(text: str, fir_id: str, store: EntityStore) -> Optional[str]:
    """Find resolved entity ID in store matching raw text from narrative."""
    clean_text = text.strip().lower()
    fir_entities = store.get_entities_by_source_fir(fir_id)

    best_id = None
    best_score = 0.0

    for ent in fir_entities:
        c_val = ent.canonical_value.lower()
        d_val = ent.display_value.lower()

        if clean_text in c_val or c_val in clean_text or clean_text in d_val or d_val in clean_text:
            return ent.id

        score_c = JaroWinkler.normalized_similarity(clean_text, c_val)
        score_d = JaroWinkler.normalized_similarity(clean_text, d_val)
        max_s = max(score_c, score_d)

        if max_s > best_score:
            best_score = max_s
            best_id = ent.id

    if best_score >= 0.75:
        return best_id
    return None


def extract_llm_relationships(
    firs: List[RawFIR],
    entity_store: EntityStore,
    client: Optional[NemotronClient] = None,
) -> List[Relationship]:
    """
    Infers narrative relationships across FIRs using Nemotron LLM and links them back to EntityStore IDs.
    """
    if client is None or not client.is_available():
        return []

    relationships: List[Relationship] = []

    for fir in firs:
        if not fir.incident_narrative:
            continue

        prompt = f"FIR Reference ID: {fir.fir_id}\nNarrative Text:\n\"\"\"\n{fir.incident_narrative}\n\"\"\""
        data = client.generate_json(prompt=prompt, system_prompt=SYSTEM_PROMPT)

        if not data or "relationships" not in data or not isinstance(data["relationships"], list):
            continue

        for r_item in data["relationships"]:
            src_txt = str(r_item.get("source_text", "")).strip()
            tgt_txt = str(r_item.get("target_text", "")).strip()
            rel_type_str = str(r_item.get("relation_type", "")).lower()
            ev_str = str(r_item.get("evidence", "")).strip()

            if not src_txt or not tgt_txt:
                continue

            try:
                rel_enum = RelationType(rel_type_str)
            except ValueError:
                rel_enum = RelationType.CONNECTED_TO

            src_id = _find_matching_entity_id(src_txt, fir.fir_id, entity_store)
            tgt_id = _find_matching_entity_id(tgt_txt, fir.fir_id, entity_store)

            if src_id and tgt_id and src_id != tgt_id:
                import uuid
                evidence_text = f"Nemotron Inferred: '{ev_str}'" if ev_str else f"LLM narrative link from FIR {fir.fir_id}"
                
                weight = EdgeWeight.calculate(
                    base_weight=0.85,
                    fir_ids=[fir.fir_id],
                    source_types=[SourceType.LLM_INFERRED.value],
                    conf1=0.85,
                    conf2=0.85,
                )

                relationships.append(
                    Relationship(
                        id=f"REL-{uuid.uuid4().hex[:8]}",
                        source_entity_id=src_id,
                        target_entity_id=tgt_id,
                        relation_type=rel_enum,
                        source_type=SourceType.LLM_INFERRED.value,
                        source_FIR_ids=[fir.fir_id],
                        evidence=evidence_text,
                        weight=weight,
                        confidence=0.85,
                    )
                )

    return relationships
