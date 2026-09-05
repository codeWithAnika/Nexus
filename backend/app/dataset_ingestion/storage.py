import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.dataset_ingestion.identity import sha256_file
from app.services.evidence_storage import STORAGE_ROOT


@dataclass(frozen=True)
class StoredImage:
    file_path: str
    sha256: str
    created: bool


def inspect_image(path: Path) -> str:
    return sha256_file(path)


def copy_image(path: Path, image_id: int, image_sha256: str) -> StoredImage:
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    filename = f"fir_dataset_{image_id}_{image_sha256[:16]}.jpg"
    destination = STORAGE_ROOT / filename
    if destination.exists():
        if sha256_file(destination) != image_sha256:
            raise OSError(f"Storage hash conflict for {destination}")
        return StoredImage(str(Path("storage") / "evidence" / filename), image_sha256, False)

    temporary_path: Path | None = None
    try:
        file_descriptor, temporary_name = tempfile.mkstemp(
            dir=STORAGE_ROOT,
            prefix=f".{filename}.",
            suffix=".tmp",
        )
        os.close(file_descriptor)
        temporary_path = Path(temporary_name)
        shutil.copyfile(path, temporary_path)
        try:
            os.link(temporary_path, destination)
        except FileExistsError:
            if sha256_file(destination) != image_sha256:
                raise OSError(f"Storage hash conflict for {destination}")
            return StoredImage(str(Path("storage") / "evidence" / filename), image_sha256, False)
        return StoredImage(str(Path("storage") / "evidence" / filename), image_sha256, True)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def remove_stored_image(file_path: str | None) -> None:
    if not file_path:
        return
    relative = Path(file_path)
    if relative.parent != Path("storage") / "evidence" or relative.name in {"", ".", ".."}:
        raise OSError("Invalid generated storage path")
    candidate = (STORAGE_ROOT / relative.name).resolve()
    root = STORAGE_ROOT.resolve()
    if candidate.parent != root:
        raise OSError("Invalid generated storage path")
    candidate.unlink(missing_ok=True)
