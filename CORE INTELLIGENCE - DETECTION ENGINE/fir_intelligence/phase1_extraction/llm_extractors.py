"""
Narrative Entity Extraction module using Nemotron LLM.
Extracts unstructured mentions from FIR incident narratives and tags them source="llm_extraction".
"""

from typing import List, Optional
from .llm_client import NemotronClient
from .models import EntityType, RawFIR, RawMention


MAP_TYPE_NAME = {
    "person": EntityType.PERSON,
    "phone": EntityType.PHONE,
    "email": EntityType.EMAIL,
    "account": EntityType.ACCOUNT,
    "organization": EntityType.ORGANIZATION,
    "location": EntityType.LOCATION,
    "device": EntityType.DEVICE,
    "ip": EntityType.IP,
    "transaction": EntityType.TRANSACTION,
    "event": EntityType.EVENT,
}


def extract_narrative_entities_llm(
    fir: Optional[RawFIR] = None,
    narrative_text: Optional[str] = None,
    source_fir_id: Optional[str] = None,
    client: Optional[NemotronClient] = None,
) -> List[RawMention]:
    """
    Extracts named entities from FIR incident narrative text using Nemotron LLM.
    Returns RawMention instances tagged with field_source="llm_extraction".
    """
    text = narrative_text or (fir.incident_narrative if fir else "")
    fir_id = source_fir_id or (fir.fir_id if fir else "")

    if client is None or not client.is_available() or not text:
        return []

    raw_entities = client.extract_narrative_entities(
        text=text,
        source_fir_id=fir_id,
    )

    mentions: List[RawMention] = []

    for item in raw_entities:
        t_str = str(item.get("type", "")).lower()
        val = str(item.get("value", "")).strip()

        if not val:
            continue

        ent_type = MAP_TYPE_NAME.get(t_str, EntityType.PERSON)

        mentions.append(
            RawMention(
                entity_type=ent_type,
                raw_value=val,
                field_source="llm_extraction",
                source_FIR_id=fir_id,
                confidence=0.85,
                context_snippet=str(item.get("context", "")) or text[:150],
            )
        )

    return mentions
