import re
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

STORAGE_ROOT = Path(__file__).resolve().parents[2] / "storage" / "evidence"
MAX_FILE_SIZE = 25 * 1024 * 1024
_SAFE_EXTENSION = re.compile(r"[^a-zA-Z0-9.]" )


class EvidenceStorageError(Exception):
    pass


def _safe_suffix(filename: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()
    suffix = _SAFE_EXTENSION.sub("", suffix)
    return suffix[:10]


async def _chunks(upload: UploadFile, chunk_size: int = 1024 * 1024) -> AsyncIterator[bytes]:
    while chunk := await upload.read(chunk_size):
        yield chunk


async def save_upload(upload: UploadFile) -> tuple[str, str, int]:
    if not upload.filename or Path(upload.filename).name != upload.filename:
        raise EvidenceStorageError("Invalid filename")

    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{_safe_suffix(upload.filename)}"
    destination = STORAGE_ROOT / stored_name
    relative_path = Path("storage") / "evidence" / stored_name
    total_size = 0

    try:
        with destination.open("wb") as output:
            async for chunk in _chunks(upload):
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    raise EvidenceStorageError("File exceeds the maximum allowed size")
                output.write(chunk)
    except EvidenceStorageError:
        destination.unlink(missing_ok=True)
        raise
    except OSError as exc:
        destination.unlink(missing_ok=True)
        raise EvidenceStorageError from exc

    return str(relative_path), upload.filename, total_size


def delete_stored_file(relative_path: str | None) -> None:
    if not relative_path:
        return
    root = STORAGE_ROOT.resolve()
    candidate = (STORAGE_ROOT.parent.parent / relative_path).resolve()
    if root not in candidate.parents:
        raise EvidenceStorageError("Invalid stored file reference")
    try:
        candidate.unlink(missing_ok=True)
    except OSError as exc:
        raise EvidenceStorageError from exc