"""
Entity deduplication module using rapidfuzz.
Deduplicates entity values that are >90% similar within the same FIR document.
"""
from typing import List
from rapidfuzz import fuzz

from processing.schema import Entity

SIMILARITY_THRESHOLD = 90.0


def deduplicate_entities(
    entities: List[Entity],
    similarity_threshold: float = SIMILARITY_THRESHOLD
) -> List[Entity]:
    """
    Deduplicate entity values that are >90% similar within the same FIR document.
    Deduplication is performed per entity type to prevent cross-category collisions.
    """
    deduped: List[Entity] = []

    for candidate in entities:
        is_duplicate = False
        cand_val = candidate.value.strip().lower()

        # Check against entities of the SAME category type already admitted
        for accepted in deduped:
            if accepted.type == candidate.type:
                accepted_val = accepted.value.strip().lower()
                # rapidfuzz ratio computes Levenshtein similarity (0.0 to 100.0)
                sim_score = fuzz.ratio(cand_val, accepted_val)
                if sim_score > similarity_threshold:
                    is_duplicate = True
                    break

        if not is_duplicate:
            deduped.append(candidate)

    return deduped
