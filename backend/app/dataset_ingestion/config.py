from pathlib import Path

DATASET_NAME = "FIR_Dataset_ICDAR2023"
EXPECTED_FIELDS = frozenset({"image_id", "bbox", "score", "category_id", "image_name", "text"})
DEFAULT_DATASET_ROOT = (
    Path(__file__).resolve().parents[3]
    / "dataset"
    / "FIR_Dataset_ICDAR2023-main"
    / "FIR_Dataset_ICDAR2023-main"
)
DEFAULT_ARCHIVE_PATH = Path(__file__).resolve().parents[3] / "dataset" / "FIR_Dataset_ICDAR2023-main.zip"
