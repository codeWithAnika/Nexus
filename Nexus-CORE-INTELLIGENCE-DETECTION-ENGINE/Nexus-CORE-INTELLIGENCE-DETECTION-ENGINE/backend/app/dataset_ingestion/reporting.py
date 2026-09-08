import json
from dataclasses import asdict
from typing import Any

from app.dataset_ingestion.models import ImportReport


def report_dict(report: ImportReport) -> dict[str, Any]:
    return asdict(report)


def report_json(report: ImportReport) -> str:
    return json.dumps(report_dict(report), default=str, indent=2)
