from __future__ import annotations

import re
from typing import NamedTuple

from app.entity_extraction.models import (
    CandidateProvenance,
    EntityCandidate,
    ExtractionEntityType,
    IdentifierCandidate,
    TextSpan,
)
from app.entity_extraction.normalizer import (
    normalize_person_name,
    normalize_police_station,
    normalize_statute,
)


class ExtractedSpanCandidate(NamedTuple):
    entity_type: ExtractionEntityType
    raw_value: str
    normalized_value: str
    span: TextSpan
    extraction_confidence: float
    extraction_method: str
    identifiers: tuple[IdentifierCandidate, ...] = ()


def extract_from_category_0(original_text: str) -> list[ExtractedSpanCandidate]:
    """Category 0 = Police Station. Default to POLICE_STATION."""
    # Find the non-whitespace span
    match = re.search(r"\S.*\S|\S", original_text)
    if not match:
        return []
    start, end = match.span()
    raw = match.group(0)
    norm = normalize_police_station(raw)
    span = TextSpan(start_char=start, end_char=end, matched_text=raw)
    return [
        ExtractedSpanCandidate(
            entity_type=ExtractionEntityType.POLICE_STATION,
            raw_value=raw,
            normalized_value=norm,
            span=span,
            extraction_confidence=0.95,
            extraction_method="category_0_police_station_rule_v1",
        )
    ]


def extract_from_category_1(original_text: str) -> list[ExtractedSpanCandidate]:
    """Category 1 = Year. Do NOT emit a standalone entity."""
    return []


def extract_from_category_2(original_text: str) -> list[ExtractedSpanCandidate]:
    """Category 2 = Statutes."""
    match = re.search(r"\S.*\S|\S", original_text)
    if not match:
        return []
    start, end = match.span()
    raw = match.group(0)
    norm = normalize_statute(raw)
    span = TextSpan(start_char=start, end_char=end, matched_text=raw)
    
    # Parse individual sections as identifiers across compound clauses
    identifiers: list[IdentifierCandidate] = []
    clauses = re.split(r"\s+(?:and|&)\s+", raw, flags=re.IGNORECASE)
    for clause in clauses:
        clause_clean = clause.strip()
        sec_match = re.match(r"^([\d\w/(),\s]+?)\s+(Ipc|Arms\s+Act|Electricity\s+Act.*)$", clause_clean, re.IGNORECASE)
        if sec_match:
            sections_str, act_name = sec_match.groups()
            act_norm = "IPC" if re.match(r"^ipc\.?$", act_name, re.IGNORECASE) else act_name.strip().upper()
            for sec in re.split(r"[/,]", sections_str):
                sec_clean = sec.strip()
                if sec_clean:
                    identifiers.append(
                        IdentifierCandidate(
                            identifier_type=f"{act_norm}_SECTION",
                            identifier_value=sec_clean,
                            normalized_value=f"{act_norm}_{sec_clean.upper()}",
                            confidence=0.98,
                        )
                    )

    return [
        ExtractedSpanCandidate(
            entity_type=ExtractionEntityType.STATUTE,
            raw_value=raw,
            normalized_value=norm,
            span=span,
            extraction_confidence=0.95,
            extraction_method="category_2_statute_rule_v1",
            identifiers=tuple(identifiers),
        )
    ]


# Honorifics, titles, and ranks that can legitimately precede names in FIR records
PREFIX_PATTERN = re.compile(
    r"^(?:(?:Sri|Smt|Smti|Md\.|Mohd\.?|Dr\.|Dr|Mr\.|Mr|Mrs\.|Mrs|Miss|Si|S\.I\.|Asi|A\.S\.I\.|Inspector|Constable)(?:\s+|$))+",
    flags=re.IGNORECASE,
)

# Obvious legal statutes, sections, and administrative/police-station terms
LEGAL_OR_ADMIN_PATTERN = re.compile(
    r"\b(?:Ipc|Act|Section|Sec|CrPC|P\.S\.?|PS|Police\s+Station)\b",
    flags=re.IGNORECASE,
)


def is_plausible_person_name(text: str) -> bool:
    """Deterministic, explainable heuristic validating that text is a plausible person-name candidate.

    Rejects:
    - Empty or whitespace-only strings
    - Purely numeric strings or calendar years
    - Strings with no alphabetic characters
    - Obvious legal statutes, acts, sections, or police station expressions
    - Strings containing only standalone titles without a trailing name
    - Strings with fewer than 2 alphabetic characters
    - Strings with no valid name tokens (at least 2 letters or an initial like 'P.')
    """
    cleaned = " ".join(text.strip().split())
    if not cleaned:
        return False
    # Reject obvious digits or 4-digit years
    if re.match(r"^\d+$", cleaned):
        return False
    # Reject strings with no alphabetic characters
    if not re.search(r"[A-Za-z]", cleaned):
        return False
    # Reject obvious statute / legal expressions or police station expressions
    if LEGAL_OR_ADMIN_PATTERN.search(cleaned):
        return False
    # Strip honorifics and ranks before validating name tokens
    stripped = PREFIX_PATTERN.sub("", cleaned).strip()
    if not stripped:
        return False
    # Must contain at least 2 alphabetic characters overall
    letters = re.findall(r"[A-Za-z]", stripped)
    if len(letters) < 2:
        return False
    # Ensure tokens contain plausible name components (at least one token with >= 2 letters or an initial)
    tokens = stripped.split()
    valid_tokens = [t for t in tokens if re.search(r"[A-Za-z]{2,}", t) or re.match(r"^[A-Za-z]\.$", t)]
    if not valid_tokens:
        return False
    return True


def extract_from_category_3(original_text: str) -> list[ExtractedSpanCandidate]:
    """Category 3 = Complainant name candidate.

    Check if it actually contains a person name.
    If multi-span contains police station or official rank, disaggregate cleanly.
    Rejects strings that fail is_plausible_person_name validation.
    """
    candidates: list[ExtractedSpanCandidate] = []
    
    # Check for multi-entity composite: "Name, PS" or "Rank Name, PS"
    ps_split = re.search(r",\s*([^,]+(?:P\.S\.?|PS|Police\s+Station).*)$", original_text, re.IGNORECASE)
    if ps_split:
        ps_start, ps_end = ps_split.span(1)
        ps_raw = ps_split.group(1).strip()
        ps_norm = normalize_police_station(ps_raw)
        # Person part is before the comma
        person_raw_full = original_text[:ps_split.start()].strip()
        p_match = re.search(r"\S.*\S|\S", person_raw_full)
        if p_match:
            p_start, p_end = p_match.span()
            p_raw = p_match.group(0)
            if is_plausible_person_name(p_raw):
                p_norm = normalize_person_name(p_raw)
                candidates.append(
                    ExtractedSpanCandidate(
                        entity_type=ExtractionEntityType.PERSON,
                        raw_value=p_raw,
                        normalized_value=p_norm,
                        span=TextSpan(start_char=p_start, end_char=p_end, matched_text=p_raw),
                        extraction_confidence=0.90,
                        extraction_method="category_3_complainant_person_split_v1",
                    )
                )
        # Add POLICE_STATION candidate
        ps_m = re.search(r"\S.*\S|\S", original_text[ps_start:ps_end])
        if ps_m:
            actual_ps_start = ps_start + ps_m.start()
            actual_ps_end = ps_start + ps_m.end()
            actual_ps_raw = original_text[actual_ps_start:actual_ps_end]
            candidates.append(
                ExtractedSpanCandidate(
                    entity_type=ExtractionEntityType.POLICE_STATION,
                    raw_value=actual_ps_raw,
                    normalized_value=ps_norm,
                    span=TextSpan(start_char=actual_ps_start, end_char=actual_ps_end, matched_text=actual_ps_raw),
                    extraction_confidence=0.92,
                    extraction_method="category_3_embedded_police_station_split_v1",
                )
            )
        return candidates

    # Single span candidate
    match = re.search(r"\S.*\S|\S", original_text)
    if not match:
        return []
    start, end = match.span()
    raw = match.group(0)
    
    # Strictly validate that the text is a plausible person-name candidate
    if not is_plausible_person_name(raw):
        return []
    
    norm = normalize_person_name(raw)
    span = TextSpan(start_char=start, end_char=end, matched_text=raw)
    
    candidates.append(
        ExtractedSpanCandidate(
            entity_type=ExtractionEntityType.PERSON,
            raw_value=raw,
            normalized_value=norm,
            span=span,
            extraction_confidence=0.92,
            extraction_method="category_3_complainant_person_rule_v1",
        )
    )
    return candidates
