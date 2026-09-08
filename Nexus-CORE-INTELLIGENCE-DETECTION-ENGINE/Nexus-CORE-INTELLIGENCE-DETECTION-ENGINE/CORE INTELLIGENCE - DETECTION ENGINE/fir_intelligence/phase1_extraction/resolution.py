"""
Entity Resolution Engine: Deduplication, Fuzzy Matching, Contextual Boosting,
and Nemotron-Augmented Ambiguous Merge Reasoning.
"""

import uuid
from typing import Dict, List, Optional, Set, Tuple
from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler

from .llm_client import NemotronClient
from .llm_merge_reasoner import evaluate_ambiguous_merge_llm
from .models import (
    CandidateMerge,
    Entity,
    EntityType,
    MergeDecision,
    RawMention,
)
from .normalizers import normalize_mention


class EntityResolver:
    """
    Core resolution engine that takes extracted RawMentions and converts them into
    deduplicated, normalized Entity models with complete auditability and optional Nemotron LLM reasoning.
    """

    def __init__(
        self,
        exact_match_types: Optional[Set[EntityType]] = None,
        fuzzy_merge_threshold: float = 0.85,
        candidate_merge_threshold: float = 0.70,
        use_llm: bool = False,
        llm_client: Optional[NemotronClient] = None,
    ):
        self.exact_match_types = exact_match_types or {
            EntityType.PHONE,
            EntityType.EMAIL,
            EntityType.IP,
            EntityType.CASE_REF,
            EntityType.ACCOUNT,
            EntityType.TRANSACTION,
            EntityType.EVENT,
        }
        self.fuzzy_merge_threshold = fuzzy_merge_threshold
        self.candidate_merge_threshold = candidate_merge_threshold
        self.use_llm = use_llm
        self.llm_client = llm_client

    def resolve_mentions(
        self, mentions: List[RawMention]
    ) -> Tuple[List[Entity], List[CandidateMerge], List[MergeDecision]]:
        """
        Main pipeline execution for entity resolution:
        1. Initial Entity creation from normalized mentions
        2. Exact match merging pass
        3. Fuzzy, Contextual & Nemotron-augmented match merging pass
        4. Candidate merge identification
        """
        proto_entities = self._create_proto_entities(mentions)
        merged_entities, exact_decisions = self._exact_match_pass(proto_entities)

        final_entities, candidate_merges, fuzzy_decisions = self._fuzzy_match_pass(
            merged_entities
        )

        all_decisions = exact_decisions + fuzzy_decisions
        return final_entities, candidate_merges, all_decisions

    def _create_proto_entities(self, mentions: List[RawMention]) -> List[Entity]:
        proto_entities: List[Entity] = []

        for mention in mentions:
            canonical, display = normalize_mention(mention)
            if not canonical:
                continue

            ent_id = f"ENT-{mention.entity_type.value.upper()}-{uuid.uuid4().hex[:8]}"
            metadata = {"created_from_field": mention.field_source}
            if "llm" in mention.field_source:
                metadata["source"] = "llm_extraction"

            proto_entities.append(
                Entity(
                    id=ent_id,
                    type=mention.entity_type,
                    canonical_value=canonical,
                    display_value=display,
                    source_FIR_ids=[mention.source_FIR_id],
                    raw_mentions=[mention],
                    confidence=mention.confidence,
                    metadata=metadata,
                    merge_history=[],
                )
            )

        return proto_entities

    def _exact_match_pass(
        self, entities: List[Entity]
    ) -> Tuple[List[Entity], List[MergeDecision]]:
        merged_buckets: Dict[Tuple[EntityType, str], Entity] = {}
        decisions: List[MergeDecision] = []

        for ent in entities:
            key = (ent.type, ent.canonical_value)
            if key in merged_buckets:
                target = merged_buckets[key]
                
                decision = MergeDecision(
                    entity_id_1=target.id,
                    entity_id_2=ent.id,
                    merged_entity_id=target.id,
                    merge_type="exact_match",
                    confidence=1.0,
                    reasoning=f"exact_match:{ent.type.value.lower()}|{ent.canonical_value}",
                )
                target.merge_history.append(decision)
                decisions.append(decision)

                for fir_id in ent.source_FIR_ids:
                    if fir_id not in target.source_FIR_ids:
                        target.source_FIR_ids.append(fir_id)
                target.raw_mentions.extend(ent.raw_mentions)
            else:
                merged_buckets[key] = ent

        return list(merged_buckets.values()), decisions

    def _fuzzy_match_pass(
        self, entities: List[Entity]
    ) -> Tuple[List[Entity], List[CandidateMerge], List[MergeDecision]]:
        by_type: Dict[EntityType, List[Entity]] = {}
        for ent in entities:
            by_type.setdefault(ent.type, []).append(ent)

        final_entities: List[Entity] = []
        all_candidates: List[CandidateMerge] = []
        all_decisions: List[MergeDecision] = []

        phone_to_source_firs, phone_to_raw_values = self._build_identifier_maps(entities)

        for ent_type, group in by_type.items():
            if ent_type not in (EntityType.PERSON, EntityType.LOCATION, EntityType.ORGANIZATION):
                final_entities.extend(group)
                continue

            merged_group, candidates, decisions = self._resolve_group(
                group, phone_to_source_firs, phone_to_raw_values
            )
            final_entities.extend(merged_group)
            all_candidates.extend(candidates)
            all_decisions.extend(decisions)

        return final_entities, all_candidates, all_decisions

    def _build_identifier_maps(
        self, entities: List[Entity]
    ) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
        phone_to_source_firs: Dict[str, Set[str]] = {}
        phone_to_raw_values: Dict[str, Set[str]] = {}

        for ent in entities:
            if ent.type == EntityType.PHONE:
                phone_to_source_firs[ent.canonical_value] = set(ent.source_FIR_ids)
                for rm in ent.raw_mentions:
                    phone_to_raw_values.setdefault(ent.canonical_value, set()).add(
                        rm.raw_value
                    )

        return phone_to_source_firs, phone_to_raw_values

    def _calculate_similarity(
        self,
        ent1: Entity,
        ent2: Entity,
        phone_to_source_firs: Dict[str, Set[str]],
    ) -> Tuple[float, str]:
        str1 = ent1.canonical_value
        str2 = ent2.canonical_value

        ts_ratio = fuzz.token_sort_ratio(str1, str2) / 100.0
        jw_ratio = JaroWinkler.normalized_similarity(str1, str2)

        base_score = 0.6 * ts_ratio + 0.4 * jw_ratio
        reasons = [f"token_sort_ratio:{ts_ratio:.2f}", f"jaro_winkler:{jw_ratio:.2f}"]

        shared_firs = set(ent1.source_FIR_ids).intersection(set(ent2.source_FIR_ids))
        context_boost = 0.0

        if shared_firs:
            context_boost += 0.10
            reasons.append(f"shared_fir:{','.join(shared_firs)}")

        for phone, fir_set in phone_to_source_firs.items():
            if fir_set.intersection(ent1.source_FIR_ids) and fir_set.intersection(
                ent2.source_FIR_ids
            ):
                context_boost += 0.15
                reasons.append(f"shared_identifier:phone|{phone}")
                break

        final_score = min(1.0, base_score + context_boost)
        reasoning = f"fuzzy_score:{final_score:.2f} (" + "; ".join(reasons) + ")"
        return final_score, reasoning

    def _resolve_group(
        self,
        group: List[Entity],
        phone_to_source_firs: Dict[str, Set[str]],
        phone_to_raw_values: Dict[str, Set[str]],
    ) -> Tuple[List[Entity], List[CandidateMerge], List[MergeDecision]]:
        active_entities = list(group)
        candidates: List[CandidateMerge] = []
        decisions: List[MergeDecision] = []

        i = 0
        while i < len(active_entities):
            j = i + 1
            merged_any = False
            while j < len(active_entities):
                ent1 = active_entities[i]
                ent2 = active_entities[j]

                score, reasoning = self._calculate_similarity(
                    ent1, ent2, phone_to_source_firs
                )

                # High confidence auto-merge
                if score >= self.fuzzy_merge_threshold:
                    merge_decision = MergeDecision(
                        entity_id_1=ent1.id,
                        entity_id_2=ent2.id,
                        merged_entity_id=ent1.id,
                        merge_type="fuzzy_match",
                        confidence=score,
                        reasoning=reasoning,
                    )
                    ent1.merge_history.append(merge_decision)
                    decisions.append(merge_decision)

                    for fir_id in ent2.source_FIR_ids:
                        if fir_id not in ent1.source_FIR_ids:
                            ent1.source_FIR_ids.append(fir_id)
                    ent1.raw_mentions.extend(ent2.raw_mentions)
                    if len(ent2.display_value) > len(ent1.display_value):
                        ent1.display_value = ent2.display_value

                    active_entities.pop(j)
                    merged_any = True

                # Borderline ambiguous match -> Optional Nemotron LLM evaluation
                elif score >= self.candidate_merge_threshold:
                    llm_merged = False
                    if self.use_llm and self.llm_client and self.llm_client.is_available():
                        # Extract raw context text from mentions
                        context_snippets = [
                            f"Mention raw value: {rm.raw_value} (Source FIR: {rm.source_FIR_id}, Field: {rm.field_source})"
                            for rm in ent1.raw_mentions + ent2.raw_mentions
                        ]
                        snippet_str = "\n".join(context_snippets)

                        llm_res = evaluate_ambiguous_merge_llm(
                            ent1=ent1,
                            ent2=ent2,
                            context_snippet=snippet_str,
                            client=self.llm_client,
                        )

                        if llm_res and llm_res.get("merge") and llm_res.get("confidence", 0) >= 0.85:
                            llm_reasoning = f"{reasoning} | Nemotron LLM Verdict: MERGE (confidence: {llm_res['confidence']:.2f}) - {llm_res['reasoning']}"
                            merge_decision = MergeDecision(
                                entity_id_1=ent1.id,
                                entity_id_2=ent2.id,
                                merged_entity_id=ent1.id,
                                merge_type="nemotron_llm_boosted_merge",
                                confidence=llm_res["confidence"],
                                reasoning=llm_reasoning,
                            )
                            ent1.merge_history.append(merge_decision)
                            decisions.append(merge_decision)

                            for fir_id in ent2.source_FIR_ids:
                                if fir_id not in ent1.source_FIR_ids:
                                    ent1.source_FIR_ids.append(fir_id)
                            ent1.raw_mentions.extend(ent2.raw_mentions)
                            if len(ent2.display_value) > len(ent1.display_value):
                                ent1.display_value = ent2.display_value

                            active_entities.pop(j)
                            merged_any = True
                            llm_merged = True

                    if not llm_merged:
                        cand = CandidateMerge(
                            entity_id_1=ent1.id,
                            entity_id_2=ent2.id,
                            entity_1_value=ent1.display_value,
                            entity_2_value=ent2.display_value,
                            entity_type=ent1.type,
                            similarity_score=score,
                            reasoning=reasoning,
                        )
                        candidates.append(cand)
                        j += 1
                else:
                    j += 1

            if not merged_any:
                i += 1

        return active_entities, candidates, decisions
