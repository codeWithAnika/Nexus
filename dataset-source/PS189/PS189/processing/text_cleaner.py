"""
Text cleaning and OCR confidence filtering.
Drops records with confidence score < 0.60 and cleans noisy OCR strings using textacy.
"""
from typing import Any, Dict, List
import textacy.preprocessing as t_prep

SCORE_THRESHOLD = 0.60


def clean_ocr_text(raw_text: str) -> str:
    """Normalize unicode, strip extraneous whitespaces and noisy OCR artifacts."""
    if not raw_text:
        return ""
    text = t_prep.normalize.unicode(raw_text)
    text = t_prep.normalize.whitespace(text)
    # Strip residual surrounding quotation marks or edge punctuation
    text = text.strip(" \t\r\n\"'")
    return text


def clean_grouped_records(
    grouped_records: Dict[str, List[Dict[str, Any]]],
    min_score: float = SCORE_THRESHOLD
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Loop through grouped records, drop any record where score < min_score (0.60),
    and clean OCR text for surviving records using textacy.
    """
    cleaned_grouped: Dict[str, List[Dict[str, Any]]] = {}

    for image_name, records in grouped_records.items():
        surviving = []
        for record in records:
            score = float(record.get("score", 0.0))
            if score >= min_score:
                rec_copy = dict(record)
                cleaned_val = clean_ocr_text(rec_copy.get("text", ""))
                if cleaned_val:
                    rec_copy["text"] = cleaned_val
                    surviving.append(rec_copy)
        cleaned_grouped[image_name] = surviving

    return cleaned_grouped
