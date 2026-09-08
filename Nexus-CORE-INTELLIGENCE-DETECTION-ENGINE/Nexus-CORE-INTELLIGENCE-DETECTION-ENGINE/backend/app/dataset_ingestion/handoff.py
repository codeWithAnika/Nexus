import json
from pathlib import Path
from typing import Iterable

from app.dataset_ingestion.models import HandoffRecord


def handoff_lines(records: Iterable[HandoffRecord]) -> str:
    return "".join(json.dumps(record.__dict__, ensure_ascii=True, separators=(",", ":")) + "\n" for record in records)


def write_handoff(records: Iterable[HandoffRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(handoff_lines(records), encoding="utf-8")
