from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import Settings, get_settings
from app.ingestion.chunking import ChunkConfigError, chunk_documents
from app.ingestion.loaders import (
    DocumentLoadError,
    discover_files,
    load_document,
)
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore


@dataclass
class IndexingSummary:
    documents_processed: int = 0
    chunks_created: int = 0
    chunks_indexed: int = 0
    unsupported_files: list[str] = field(default_factory=list)
    skipped_or_failed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def print_report(self) -> None:
        print("\n=== Indexing summary ===")
        print(f"Documents processed : {self.documents_processed}")
        print(f"Chunks created      : {self.chunks_created}")
        print(f"Chunks indexed      : {self.chunks_indexed}")
        print(f"Unsupported files   : {len(self.unsupported_files)}")
        if self.unsupported_files:
            for name in self.unsupported_files:
                print(f"  - skipped (unsupported): {name}")
        if self.skipped_or_failed:
            print(f"Failed/skipped docs : {len(self.skipped_or_failed)}")
            for name in self.skipped_or_failed:
                print(f"  - {name}")
        if self.errors:
            print("Errors:")
            for message in self.errors:
                print(f"  - {message}")
        print("========================\n")


def index_documents(
    path: Path,
    settings: Settings | None = None,
    *,
    clean: bool = False,
) -> IndexingSummary:
    """Load → chunk → embed → upsert into the persistent vector store."""
    settings = settings or get_settings()
    summary = IndexingSummary()

    try:
        supported, unsupported = discover_files(path)
    except (FileNotFoundError, NotADirectoryError) as exc:
        summary.errors.append(str(exc))
        return summary

    summary.unsupported_files = [file.name for file in unsupported]

    if not supported and not unsupported:
        summary.errors.append(f"Directory is empty: {path}")
        return summary

    if not supported:
        summary.errors.append(
            f"No supported documents found in {path} "
            f"(supported: .txt, .md, .pdf)"
        )
        return summary

    try:
        embedding_service = EmbeddingService(settings.embedding_model_name)
        vector_store = VectorStore(
            persist_path=settings.vector_db_path,
            collection_name=settings.collection_name,
        )
        if clean:
            vector_store.clear()
            print(
                f"Cleared existing collection '{settings.collection_name}' "
                f"at {settings.vector_db_path} before indexing."
            )
    except Exception as exc:  # noqa: BLE001
        summary.errors.append(f"Failed to initialise embedding/vector services: {exc}")
        return summary

    all_chunks = []

    for file_path in supported:
        try:
            loaded = load_document(file_path)
            chunks = chunk_documents(
                loaded,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )
            if not chunks:
                summary.skipped_or_failed.append(
                    f"{file_path.name} (no non-empty chunks)"
                )
                continue
            all_chunks.extend(chunks)
            summary.documents_processed += 1
            summary.chunks_created += len(chunks)
            print(
                f"Loaded {file_path.name}: "
                f"{len(loaded)} text unit(s), {len(chunks)} chunk(s)"
            )
        except (DocumentLoadError, ChunkConfigError) as exc:
            summary.skipped_or_failed.append(file_path.name)
            summary.errors.append(str(exc))
        except Exception as exc:  # noqa: BLE001
            summary.skipped_or_failed.append(file_path.name)
            summary.errors.append(f"Unexpected error for {file_path.name}: {exc}")

    if not all_chunks:
        if not summary.errors:
            summary.errors.append("No chunks were created from the input documents.")
        return summary

    try:
        texts = [chunk.text for chunk in all_chunks]
        embeddings = embedding_service.embed_texts(texts)
        indexed = vector_store.upsert_chunks(
            ids=[chunk.id for chunk in all_chunks],
            documents=texts,
            embeddings=embeddings,
            metadatas=[dict(chunk.metadata) for chunk in all_chunks],
        )
        summary.chunks_indexed = indexed
        print(
            f"Upserted {indexed} chunk(s) into collection "
            f"'{settings.collection_name}' at {settings.vector_db_path}"
        )
        print(f"Collection size now: {vector_store.count}")
    except Exception as exc:  # noqa: BLE001
        summary.errors.append(f"Vector store failure: {exc}")

    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Index local documents into ChromaDB: "
            "load → chunk → embed → persistent vector store."
        )
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Directory of documents (.txt, .md, .pdf). Defaults to DOCUMENTS_PATH.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clear existing vector collection before indexing to prevent stale chunks.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = get_settings()
    except Exception as exc:  # noqa: BLE001
        print(f"Invalid configuration: {exc}", file=sys.stderr)
        return 1

    path = (args.path or settings.documents_path).resolve()
    print(f"Indexing documents from: {path}")
    print(f"Embedding model: {settings.embedding_model_name}")
    print(
        f"Chunk size={settings.chunk_size}, overlap={settings.chunk_overlap}"
    )
    print(f"Vector DB path: {settings.vector_db_path}")
    print(f"Collection: {settings.collection_name}")
    if args.clean:
        print("Mode: clean re-index (clearing collection first)")

    summary = index_documents(path, settings=settings, clean=args.clean)
    summary.print_report()

    if summary.errors and summary.chunks_indexed == 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
