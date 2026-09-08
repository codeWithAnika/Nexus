"""
Dataset loader for ingesting and grouping FIR OCR records.
"""
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def resolve_dataset_path(path_hint: Optional[Union[str, Path]] = None) -> Path:
    """Resolve the path to FIR_details.json across standard workspace locations."""
    if path_hint:
        p = Path(path_hint)
        if p.exists():
            return p

    candidates = [
        Path("FIR_details.json"),
        Path("FIR_Dataset_ICDAR2023-main/FIR_Dataset_ICDAR2023-main/FIR_details.json"),
        Path(__file__).resolve().parent.parent / "FIR_details.json",
        Path(__file__).resolve().parent.parent / "FIR_Dataset_ICDAR2023-main/FIR_Dataset_ICDAR2023-main/FIR_details.json",
    ]
    for cand in candidates:
        if cand.exists():
            return cand

    raise FileNotFoundError(
        "Could not find FIR_details.json. Searched locations: "
        + ", ".join(str(c) for c in candidates)
    )


def load_dataset(file_path: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
    """Load raw records from FIR_details.json."""
    resolved_path = resolve_dataset_path(file_path)
    with open(resolved_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list of records in {resolved_path}, got {type(data)}")
    return data


def group_by_image(records: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group OCR records by image_name."""
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        image_name = record.get("image_name")
        if not image_name:
            continue
        grouped[image_name].append(record)
    return dict(grouped)


def load_and_group_fir_details(file_path: Optional[Union[str, Path]] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Convenience entrypoint to load FIR_details.json and return records grouped by image_name."""
    records = load_dataset(file_path)
    return group_by_image(records)
