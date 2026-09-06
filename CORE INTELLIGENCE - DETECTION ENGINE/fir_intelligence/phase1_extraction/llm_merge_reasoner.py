"""
Nemotron-augmented ambiguous merge reasoning.
Evaluates borderline fuzzy entity matches with context to decide whether two entities refer to the same entity.
"""

from typing import Any, Dict, Optional
from .llm_client import NemotronClient
from .models import Entity


SYSTEM_PROMPT = """
You are an expert criminal intelligence entity resolution analyst.
Your task is to determine whether two entity records extracted from First Information Reports (FIRs) refer to the exact same real-world person, location, or organization.

Examine the entity details and the provided FIR narrative contexts carefully.

Respond ONLY with a JSON object matching this exact schema:
{
  "merge": true | false,
  "confidence": 0.0 to 1.0,
  "reasoning": "Concise 1-2 sentence explanation detailing why these entities should or should not be merged."
}
"""


def evaluate_ambiguous_merge_llm(
    ent1: Entity,
    ent2: Entity,
    context_snippet: str,
    client: Optional[NemotronClient] = None,
) -> Optional[Dict[str, Any]]:
    """
    Evaluates whether two candidate entities refer to the same entity using Nemotron.
    Returns dict with keys ('merge', 'confidence', 'reasoning') or None if evaluation fails/unavailable.
    """
    if client is None or not client.is_available():
        return None

    prompt = f"""
Entity 1:
- Type: {ent1.type.value}
- Canonical Value: {ent1.canonical_value}
- Display Value: {ent1.display_value}
- Source FIRs: {', '.join(ent1.source_FIR_ids)}

Entity 2:
- Type: {ent2.type.value}
- Canonical Value: {ent2.canonical_value}
- Display Value: {ent2.display_value}
- Source FIRs: {', '.join(ent2.source_FIR_ids)}

Shared Context & FIR Snippets:
\"\"\"
{context_snippet.strip() if context_snippet else 'No additional context available.'}
\"\"\"

Should Entity 1 and Entity 2 be merged into a single canonical entity?
"""

    try:
        data = client.generate_json(prompt=prompt, system_prompt=SYSTEM_PROMPT)
        if not data or "merge" not in data or "reasoning" not in data:
            return None

        return {
            "merge": bool(data.get("merge", False)),
            "confidence": float(data.get("confidence", 0.5)),
            "reasoning": str(data.get("reasoning", "")).strip(),
        }

    except Exception as e:
        print(f"Warning: Nemotron merge evaluation failed for {ent1.id} vs {ent2.id}: {e}")
        return None
