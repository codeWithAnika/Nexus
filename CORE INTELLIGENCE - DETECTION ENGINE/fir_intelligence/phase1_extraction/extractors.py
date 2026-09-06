"""
Rule and regex-based extractors for extracting structured identifiers from text,
with optional Nemotron LLM augmentation for free-text narrative NER.
Each extractor is an independently testable function.
"""

import re
from typing import List, Optional, Tuple
from .llm_client import NemotronClient
from .llm_extractors import extract_narrative_entities_llm
from .models import EntityType, RawFIR, RawMention


# Regular expression patterns
PHONE_REGEX = re.compile(
    r'(?:\+?91[\s\-]?)?(?:[0]?[6-9]\d{9}|[6-9]\d{4}[\s\-]?\d{5})'
)

EMAIL_REGEX = re.compile(
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
)

DATE_REGEX = re.compile(
    r'\b(?:\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}|\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}|\d{1,2}(?:st|nd|rd|th)?[\s\-]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,\-]+\d{2,4})\b',
    re.IGNORECASE
)

AMOUNT_REGEX = re.compile(
    r'(?:(?:Rs\.?|INR|₹)\s*[\d,]+(?:\.\d+)?(?:\s*(?:lakh|lakhs|crore|crores|k|thousand))?|[\d,]+(?:\.\d+)?\s*(?:lakh|lakhs|crore|crores)\b)',
    re.IGNORECASE
)

CASE_REF_REGEX = re.compile(
    r'\b(?:FIR|Crime|Case)\s*(?:No\.?|Num\.?|Ref\.?)?\s*[:\-]?\s*[A-Z0-9/-]{3,20}\b',
    re.IGNORECASE
)

IPV4_REGEX = re.compile(
    r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
)

IPV6_REGEX = re.compile(
    r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
)


def extract_phones(text: str) -> List[str]:
    """Extract raw phone number strings from input text."""
    if not text:
        return []
    matches = PHONE_REGEX.findall(text)
    cleaned = []
    for m in matches:
        m_str = m.strip()
        if len(re.sub(r'\D', '', m_str)) >= 10:
            cleaned.append(m_str)
    return list(dict.fromkeys(cleaned))


def extract_emails(text: str) -> List[str]:
    """Extract email address strings from input text."""
    if not text:
        return []
    matches = EMAIL_REGEX.findall(text)
    return list(dict.fromkeys([m.strip() for m in matches]))


def extract_dates(text: str) -> List[str]:
    """Extract date strings from input text."""
    if not text:
        return []
    matches = DATE_REGEX.findall(text)
    return list(dict.fromkeys([m.strip() for m in matches]))


def extract_amounts(text: str) -> List[str]:
    """Extract monetary amount strings from input text."""
    if not text:
        return []
    matches = AMOUNT_REGEX.findall(text)
    return list(dict.fromkeys([m.strip() for m in matches]))


def extract_case_refs(text: str) -> List[str]:
    """Extract FIR/Case reference numbers from input text."""
    if not text:
        return []
    matches = CASE_REF_REGEX.findall(text)
    return list(dict.fromkeys([m.strip() for m in matches]))


def extract_ips(text: str) -> List[str]:
    """Extract IPv4 and IPv6 addresses from input text."""
    if not text:
        return []
    v4 = IPV4_REGEX.findall(text)
    v6 = IPV6_REGEX.findall(text)
    all_ips = v4 + v6
    return list(dict.fromkeys([m.strip() for m in all_ips]))


def extract_all_mentions(
    fir: RawFIR,
    use_llm: bool = False,
    llm_client: Optional[NemotronClient] = None,
) -> List[RawMention]:
    """
    Orchestrate extraction of structured fields and narrative free-text.
    Attaches source_FIR_id and field_source to every extracted item for explainability.
    Optionally calls Nemotron for advanced narrative NER when use_llm=True.
    """
    mentions: List[RawMention] = []
    fir_id = fir.case_ref

    # 1. FIR Case Reference itself as an entity
    mentions.append(RawMention(
        entity_type=EntityType.CASE_REF,
        raw_value=fir.case_ref,
        source_FIR_id=fir_id,
        field_source="case_ref",
        confidence=1.0
    ))

    # 2. Structured Person: Complainant
    if fir.complainant_name and fir.complainant_name.strip():
        mentions.append(RawMention(
            entity_type=EntityType.PERSON,
            raw_value=fir.complainant_name.strip(),
            source_FIR_id=fir_id,
            field_source="complainant_name",
            confidence=0.95
        ))

    # 3. Structured Location: Complainant Address
    if fir.complainant_address and fir.complainant_address.strip():
        mentions.append(RawMention(
            entity_type=EntityType.LOCATION,
            raw_value=fir.complainant_address.strip(),
            source_FIR_id=fir_id,
            field_source="complainant_address",
            confidence=0.90
        ))

    # 4. Structured Person: Accused
    if fir.accused_name:
        names = fir.accused_name if isinstance(fir.accused_name, list) else [fir.accused_name]
        for name in names:
            if name and str(name).strip():
                mentions.append(RawMention(
                    entity_type=EntityType.PERSON,
                    raw_value=str(name).strip(),
                    source_FIR_id=fir_id,
                    field_source="accused_name",
                    confidence=0.95
                ))

    # 5. Structured Location: Accused Address
    if fir.accused_address and fir.accused_address.strip():
        mentions.append(RawMention(
            entity_type=EntityType.LOCATION,
            raw_value=fir.accused_address.strip(),
            source_FIR_id=fir_id,
            field_source="accused_address",
            confidence=0.90
        ))

    # 6. Structured Phone numbers mentioned field
    for phone in fir.phone_numbers_mentioned:
        if phone and phone.strip():
            mentions.append(RawMention(
                entity_type=EntityType.PHONE,
                raw_value=phone.strip(),
                source_FIR_id=fir_id,
                field_source="phone_numbers_mentioned",
                confidence=1.0
            ))

    # 7. Structured Monetary amounts mentioned field
    for amt in fir.amounts_mentioned:
        if amt and amt.strip():
            mentions.append(RawMention(
                entity_type=EntityType.TRANSACTION,
                raw_value=amt.strip(),
                source_FIR_id=fir_id,
                field_source="amounts_mentioned",
                confidence=1.0
            ))

    # 8. Extract from free-text narrative_text (Deterministic Regex)
    narrative = fir.narrative_text or ""
    if narrative.strip():
        for p in extract_phones(narrative):
            mentions.append(RawMention(
                entity_type=EntityType.PHONE,
                raw_value=p,
                source_FIR_id=fir_id,
                field_source="narrative_text",
                confidence=0.90
            ))
            
        for e in extract_emails(narrative):
            mentions.append(RawMention(
                entity_type=EntityType.EMAIL,
                raw_value=e,
                source_FIR_id=fir_id,
                field_source="narrative_text",
                confidence=0.95
            ))

        for d in extract_dates(narrative):
            mentions.append(RawMention(
                entity_type=EntityType.EVENT,
                raw_value=d,
                source_FIR_id=fir_id,
                field_source="narrative_text",
                confidence=0.85
            ))

        for a in extract_amounts(narrative):
            mentions.append(RawMention(
                entity_type=EntityType.TRANSACTION,
                raw_value=a,
                source_FIR_id=fir_id,
                field_source="narrative_text",
                confidence=0.90
            ))

        for cr in extract_case_refs(narrative):
            if cr.lower() != fir.case_ref.lower():
                mentions.append(RawMention(
                    entity_type=EntityType.CASE_REF,
                    raw_value=cr,
                    source_FIR_id=fir_id,
                    field_source="narrative_text",
                    confidence=0.90
                ))

        for ip in extract_ips(narrative):
            mentions.append(RawMention(
                entity_type=EntityType.IP,
                raw_value=ip,
                source_FIR_id=fir_id,
                field_source="narrative_text",
                confidence=0.95
            ))

    # 9. Nemotron LLM-Augmented Narrative Extraction (Optional)
    if use_llm and llm_client and narrative.strip():
        llm_mentions = extract_narrative_entities_llm(
            narrative_text=narrative,
            source_fir_id=fir_id,
            client=llm_client,
        )
        mentions.extend(llm_mentions)

    # Deduplicate identical mentions
    unique_mentions: List[RawMention] = []
    seen = set()
    for m in mentions:
        key = (m.entity_type, m.raw_value.lower(), m.source_FIR_id, m.field_source)
        if key not in seen:
            seen.add(key)
            unique_mentions.append(m)

    return unique_mentions
