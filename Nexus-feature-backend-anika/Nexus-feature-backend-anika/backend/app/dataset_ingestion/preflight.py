import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from app.dataset_ingestion.config import EXPECTED_FIELDS
from app.dataset_ingestion.models import AnnotatedImage, OCRInput, PreflightReport

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


class PreflightError(ValueError):
    pass


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _filename_pattern(name: str) -> str:
    stem = Path(name).stem
    stem = re.sub(r"__\d+$", "", stem)
    if "%20" in stem:
        return "encoded-or-ambiguous"
    if re.fullmatch(r".+\s+PS\d+", stem, re.IGNORECASE):
        return "station-plus-numeric-token"
    if re.fullmatch(r".+\s+PS.+-\d{2,4}-\d{3,5}", stem, re.IGNORECASE):
        return "station-code-year-number-like"
    if re.fullmatch(r".+\s+PS.+", stem, re.IGNORECASE):
        return "station-plus-other-token"
    return "no-recognized-PS-pattern"


def run_preflight(dataset_root: Path) -> PreflightReport:
    dataset_root = dataset_root.resolve()
    json_path = dataset_root / "FIR_details.json"
    image_root = dataset_root / "FIR_images_v1"
    if not dataset_root.is_dir():
        raise PreflightError(f"Dataset root does not exist: {dataset_root}")
    if not json_path.is_file():
        raise PreflightError(f"OCR JSON does not exist: {json_path}")
    if not image_root.is_dir():
        raise PreflightError(f"Image directory does not exist: {image_root}")

    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PreflightError(f"Unable to read OCR JSON: {exc}") from exc
    if not isinstance(payload, list):
        raise PreflightError("OCR JSON must be a flat array")

    disk_images = sorted(
        path for path in image_root.rglob("*") if path.is_file() and path.suffix.lower() in _IMAGE_EXTENSIONS
    )
    disk_by_name: dict[str, list[Path]] = defaultdict(list)
    for path in disk_images:
        disk_by_name[path.name].append(path)
    duplicate_disk_names = sorted(name for name, paths in disk_by_name.items() if len(paths) > 1)
    if duplicate_disk_names:
        raise PreflightError(f"Duplicate image basenames on disk: {duplicate_disk_names[:5]}")

    grouped: dict[int, list[OCRInput]] = defaultdict(list)
    id_names: dict[int, set[str]] = defaultdict(set)
    name_ids: dict[str, set[int]] = defaultdict(set)
    categories: Counter[int] = Counter()
    scores: list[float] = []
    suspicious: list[str] = []
    for source_index, record in enumerate(payload):
        if not isinstance(record, dict) or set(record) != EXPECTED_FIELDS:
            raise PreflightError(f"Record {source_index} does not have exactly the expected fields")
        image_id = record["image_id"]
        image_name = record["image_name"]
        bbox = record["bbox"]
        score = record["score"]
        category_id = record["category_id"]
        text = record["text"]
        if not isinstance(image_id, int) or isinstance(image_id, bool) or image_id < 0:
            raise PreflightError(f"Invalid image_id at record {source_index}")
        if not isinstance(image_name, str) or not image_name.strip() or Path(image_name).name != image_name:
            raise PreflightError(f"Invalid image_name at record {source_index}")
        if not isinstance(bbox, list) or len(bbox) != 4 or not all(_number(value) for value in bbox):
            raise PreflightError(f"Invalid bbox at record {source_index}")
        if bbox[2] < bbox[0] or bbox[3] < bbox[1]:
            raise PreflightError(f"Reversed bbox at record {source_index}")
        if not _number(score) or not 0 <= score <= 1:
            raise PreflightError(f"Invalid score at record {source_index}")
        if not isinstance(category_id, int) or isinstance(category_id, bool):
            raise PreflightError(f"Invalid category_id at record {source_index}")
        if not isinstance(text, str):
            raise PreflightError(f"Invalid text at record {source_index}: expected a string")
        if not text.strip():
            suspicious.append(f"record {source_index}: empty text")
        if image_name not in disk_by_name:
            raise PreflightError(f"Referenced image is missing: {image_name}")
        item = OCRInput(source_index, image_id, image_name, tuple(float(value) for value in bbox), float(score), category_id, text)
        grouped[image_id].append(item)
        id_names[image_id].add(image_name)
        name_ids[image_name].add(image_id)
        categories[category_id] += 1
        scores.append(float(score))

    conflicting_ids = {key: value for key, value in id_names.items() if len(value) > 1}
    conflicting_names = {key: value for key, value in name_ids.items() if len(value) > 1}
    if conflicting_ids or conflicting_names:
        raise PreflightError(f"Conflicting image identity mappings: ids={conflicting_ids}, names={conflicting_names}")

    images = tuple(
        AnnotatedImage(image_id=image_id, image_name=records[0].image_name, path=disk_by_name[records[0].image_name][0], records=tuple(records))
        for image_id, records in sorted(grouped.items())
    )
    duplicate_ocr_records = sum(
        count - 1
        for records in grouped.values()
        for count in Counter(record.text for record in records).values()
        if count > 1
    )
    return PreflightReport(
        dataset_root=dataset_root,
        json_path=json_path,
        image_count_on_disk=len(disk_images),
        annotated_image_count=len(images),
        ocr_record_count=len(payload),
        unreferenced_images=tuple(sorted(set(disk_by_name) - set(name_ids))),
        category_distribution=dict(sorted(categories.items())),
        score_min=min(scores) if scores else None,
        score_max=max(scores) if scores else None,
        duplicate_ocr_records=duplicate_ocr_records,
        suspicious_records=tuple(suspicious),
        filename_patterns=dict(Counter(_filename_pattern(image.image_name) for image in images)),
        images=images,
    )
