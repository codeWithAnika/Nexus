from collections.abc import Iterable
from statistics import median

from app.dataset_ingestion.models import OCRInput, OCRReconstruction, OCRToken


def normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def reconstruct_ocr(records: Iterable[OCRInput]) -> OCRReconstruction:
    tokens = [
        OCRToken(
            source_index=record.source_index,
            bbox=record.bbox,
            score=record.score,
            category_id=record.category_id,
            original_text=record.text,
            normalized_text=normalize_text(record.text),
            height=record.bbox[3] - record.bbox[1],
            vertical_center=(record.bbox[1] + record.bbox[3]) / 2,
        )
        for record in records
    ]
    if not tokens:
        return OCRReconstruction(extracted_text="", records=())

    tolerance = max(2.0, median(token.height for token in tokens) * 0.5)
    lines: list[list[OCRToken]] = []
    line_centers: list[float] = []
    for token in sorted(tokens, key=lambda item: (item.vertical_center, item.bbox[0], item.source_index)):
        candidates = [
            (abs(line_centers[index] - token.vertical_center), index)
            for index in range(len(lines))
            if abs(line_centers[index] - token.vertical_center) <= tolerance
        ]
        if candidates:
            _, line_index = min(candidates)
            lines[line_index].append(token)
            line_centers[line_index] = sum(item.vertical_center for item in lines[line_index]) / len(lines[line_index])
        else:
            lines.append([token])
            line_centers.append(token.vertical_center)

    ordered_lines = sorted(
        lines,
        key=lambda line: (sum(item.vertical_center for item in line) / len(line), min(item.bbox[0] for item in line)),
    )
    ordered_tokens = [
        token
        for line in ordered_lines
        for token in sorted(line, key=lambda item: (item.bbox[0], item.bbox[1], item.source_index))
    ]
    reconstructed = tuple(
        OCRToken(
            source_index=token.source_index,
            bbox=token.bbox,
            score=token.score,
            category_id=token.category_id,
            original_text=token.original_text,
            normalized_text=token.normalized_text,
            height=token.height,
            vertical_center=token.vertical_center,
            reconstructed_order=order,
        )
        for order, token in enumerate(ordered_tokens)
    )
    return OCRReconstruction(
        extracted_text=" ".join(token.normalized_text for token in reconstructed if token.normalized_text),
        records=reconstructed,
    )
