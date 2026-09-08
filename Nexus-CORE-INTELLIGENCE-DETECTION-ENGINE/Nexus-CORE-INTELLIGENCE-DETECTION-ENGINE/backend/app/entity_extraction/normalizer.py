from __future__ import annotations

import re


def normalize_whitespace(text: str) -> str:
    return " ".join(text.strip().split())


def normalize_person_name(raw: str) -> str:
    cleaned = normalize_whitespace(raw)
    if not cleaned:
        return ""
    # Strip known prefixes/titles at the start of name
    prefix_pattern = re.compile(
        r"^(?:(?:Sri|Smt|Smti|Md\.|Mohd\.?|Dr\.|Mr\.|Mrs\.|Miss|Si|S\.I\.|Asi|A\.S\.I\.|Inspector|Constable)\s+)+",
        flags=re.IGNORECASE,
    )
    stripped = prefix_pattern.sub("", cleaned).strip()
    if not stripped:
        stripped = cleaned
    # Standard Title Case for words while preserving initials like P.K.
    words = stripped.split()
    normalized_words = []
    for word in words:
        if re.match(r"^[A-Za-z]\.(?:[A-Za-z]\.)*$", word):
            normalized_words.append(word.upper())
        elif re.match(r"^[A-Z]+$", word) and len(word) > 1:
            normalized_words.append(word.capitalize())
        else:
            normalized_words.append(word.capitalize() if word.islower() else word)
    res = " ".join(normalized_words)
    return res if res else raw


def normalize_police_station(raw: str) -> str:
    cleaned = normalize_whitespace(raw)
    if not cleaned:
        return ""
    # Strip trailing punctuation
    cleaned = cleaned.rstrip(",.-_")
    # Standardize PS suffixes
    cleaned = re.sub(r"\b(?:P\.S\.?|PS|Police\s+Station)\b", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = normalize_whitespace(cleaned)
    if not cleaned:
        return raw.strip()
    return f"{cleaned.title()} Police Station"


def normalize_statute(raw: str) -> str:
    cleaned = normalize_whitespace(raw)
    if not cleaned:
        return ""
    # Split compound clauses joined by 'and' or '&', e.g. "399/402 Ipc And 25(I)(A)/27 Arms Act"
    clauses = re.split(r"\s+(?:and|&)\s+", cleaned, flags=re.IGNORECASE)
    normalized_clauses = []
    for clause in clauses:
        clause_clean = clause.strip()
        match = re.match(r"^([\d\w/(),\s]+?)\s+(Ipc|Arms\s+Act|Electricity\s+Act|Disaster\s+Management\s+Act.*)$", clause_clean, re.IGNORECASE)
        if match:
            sections_part, act_part = match.groups()
            act_norm = "IPC" if re.match(r"^ipc\.?$", act_part, re.IGNORECASE) else normalize_whitespace(act_part).upper()
            secs = [s.strip() for s in re.split(r"[/,]", sections_part) if s.strip()]
            if secs:
                normalized_clauses.extend(f"{act_norm}_{sec.upper()}" for sec in secs)
            else:
                normalized_clauses.append(clause_clean)
        else:
            normalized_clauses.append(clause_clean)
    if normalized_clauses:
        return " | ".join(normalized_clauses)
    return cleaned
