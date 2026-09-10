from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


@dataclass(frozen=True)
class LoadedDocument:
    """A unit of extracted text with source metadata.

    For PDFs, one LoadedDocument is produced per page when text is available.
    For .txt/.md, one LoadedDocument covers the whole file.
    """

    text: str
    source: str
    doc_type: str
    page_number: int | None = None


class DocumentLoadError(Exception):
    """Raised when a supported file cannot be read or has no extractable text."""


def discover_files(directory: Path) -> tuple[list[Path], list[Path]]:
    """Return (supported_files, unsupported_files) under directory (non-recursive)."""
    if not directory.exists():
        raise FileNotFoundError(f"Path does not exist: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory}")

    supported: list[Path] = []
    unsupported: list[Path] = []
    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            supported.append(path)
        else:
            unsupported.append(path)
    return supported, unsupported


def load_document(path: Path) -> list[LoadedDocument]:
    """Load text from a single supported file. Raises DocumentLoadError on failure."""
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise DocumentLoadError(f"Unsupported file type: {path.name}")

    try:
        if suffix in {".txt", ".md"}:
            return [_load_plain_text(path, doc_type=suffix.lstrip("."))]
        if suffix == ".pdf":
            return _load_pdf(path)
    except DocumentLoadError:
        raise
    except OSError as exc:
        raise DocumentLoadError(f"Cannot read file {path.name}: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 - surface unexpected parse errors clearly
        raise DocumentLoadError(f"Failed to load {path.name}: {exc}") from exc

    raise DocumentLoadError(f"Unsupported file type: {path.name}")


def _load_plain_text(path: Path, doc_type: str) -> LoadedDocument:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise DocumentLoadError(f"File is empty: {path.name}")
    return LoadedDocument(
        text=text,
        source=str(path.resolve()),
        doc_type=doc_type,
        page_number=None,
    )


def _load_pdf(path: Path) -> list[LoadedDocument]:
    reader = PdfReader(str(path))
    documents: list[LoadedDocument] = []

    for index, page in enumerate(reader.pages, start=1):
        extracted = page.extract_text() or ""
        text = extracted.strip()
        if not text:
            continue
        documents.append(
            LoadedDocument(
                text=text,
                source=str(path.resolve()),
                doc_type="pdf",
                page_number=index,
            )
        )

    if not documents:
        raise DocumentLoadError(
            f"PDF has no extractable text (may be scanned/image-only): {path.name}"
        )
    return documents
