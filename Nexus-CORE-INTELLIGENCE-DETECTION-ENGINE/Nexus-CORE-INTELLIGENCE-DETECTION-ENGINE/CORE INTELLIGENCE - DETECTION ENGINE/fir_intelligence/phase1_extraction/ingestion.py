"""
Ingestion layer for loading FIR records from JSON or CSV into RawFIR models.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Union
import pandas as pd

from .models import RawFIR


def load_fir_from_dict(data: Dict[str, Any], index_fallback: int = 1) -> RawFIR:
    """
    Parse a single dictionary into a RawFIR model, supporting standard FIR schema
    as well as structured_evidence_output.json schema from Aayush's work dataset.
    """
    cleaned_data = {k: v for k, v in data.items() if v is not None}
    
    # Handle case_ref / fir_id mapping
    fir_ref = cleaned_data.get("case_ref") or cleaned_data.get("fir_id")
    if not fir_ref or not str(fir_ref).strip():
        fir_ref = f"FIR-UNKNOWN-{index_fallback:04d}"
    cleaned_data["case_ref"] = str(fir_ref).strip()

    # Handle structured_evidence_output.json entity list mapping
    if "entities" in cleaned_data and isinstance(cleaned_data["entities"], list):
        persons = []
        locations = []
        phones = []
        dates = []
        crimes = []

        for ent in cleaned_data["entities"]:
            if isinstance(ent, dict):
                e_type = str(ent.get("type", "")).upper()
                e_val = str(ent.get("value", "")).strip()
                if not e_val:
                    continue
                if e_type in ("PERSON", "NAME", "ACCUSED", "SUSPECT"):
                    persons.append(e_val)
                elif e_type in ("LOCATION", "ADDRESS", "PLACE"):
                    locations.append(e_val)
                elif e_type in ("PHONE", "MOBILE", "CONTACT"):
                    phones.append(e_val)
                elif e_type in ("DATE", "TIME"):
                    dates.append(e_val)
                elif e_type in ("CRIME TYPE", "CRIME", "SECTION", "OFFENCE"):
                    crimes.append(e_val)

        if persons:
            cleaned_data.setdefault("accused_name", persons[0])
            cleaned_data.setdefault("accused_names_mentioned", persons)
        if locations:
            cleaned_data.setdefault("complainant_address", locations[0])
            cleaned_data.setdefault("addresses_mentioned", locations)
        if phones:
            cleaned_data.setdefault("phone_numbers_mentioned", phones)
        if dates:
            cleaned_data.setdefault("date", dates[0])
        if crimes:
            narrative = f"Offence/Crime Type: {', '.join(crimes)}."
            cleaned_data.setdefault("incident_narrative", narrative)

    return RawFIR(**cleaned_data)


def load_firs_from_json(input_data: Union[str, Path, List[Dict[str, Any]]]) -> List[RawFIR]:
    """
    Load FIR records from a JSON file path, JSON string, or a list of dicts.
    """
    if isinstance(input_data, (str, Path)):
        path = Path(input_data)
        if path.exists() and path.is_file():
            with open(path, "r", encoding="utf-8") as f:
                raw_json = json.load(f)
        else:
            # Assume input_data is raw JSON string if not an existing file
            raw_json = json.loads(str(input_data))
    elif isinstance(input_data, list):
        raw_json = input_data
    else:
        raise ValueError(f"Unsupported input type for JSON FIR loader: {type(input_data)}")

    if isinstance(raw_json, dict):
        raw_json = [raw_json]

    firs: List[RawFIR] = []
    for idx, record in enumerate(raw_json, start=1):
        try:
            fir = load_fir_from_dict(record, index_fallback=idx)
            firs.append(fir)
        except Exception as e:
            # Log error or raise depending on context; here we tolerate bad records gracefully
            print(f"Warning: Failed to parse FIR record at index {idx}: {e}")
            
    return firs


def load_firs_from_csv(filepath: Union[str, Path]) -> List[RawFIR]:
    """
    Load FIR records from a CSV file using pandas I/O.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")

    # Read CSV, filling NA values appropriately
    df = pd.read_csv(path)
    df = df.where(pd.notnull(df), None)

    records = df.to_dict(orient="records")
    firs: List[RawFIR] = []
    
    for idx, record in enumerate(records, start=1):
        # Convert non-None record entries to dict
        cleaned_record = {}
        for k, v in record.items():
            if v is not None and not (isinstance(v, float) and pd.isna(v)):
                cleaned_record[k] = v
                
        try:
            fir = load_fir_from_dict(cleaned_record, index_fallback=idx)
            firs.append(fir)
        except Exception as e:
            print(f"Warning: Failed to parse CSV FIR row {idx}: {e}")

    return firs
