from app.ingestion.chunking import (
    ChunkConfigError,
    chunk_document,
    make_chunk_id,
    validate_chunk_config,
)
from app.ingestion.loaders import LoadedDocument


def _doc(text: str, source: str = "/tmp/sample.md") -> LoadedDocument:
    return LoadedDocument(text=text, source=source, doc_type="md", page_number=None)


def test_empty_text_returns_no_chunks() -> None:
    assert chunk_document(_doc("   "), chunk_size=50, chunk_overlap=10) == []


def test_normal_chunk_creation_and_metadata() -> None:
    text = "A" * 120
    chunks = chunk_document(_doc(text, source="/data/demo.md"), chunk_size=50, chunk_overlap=10)
    assert len(chunks) >= 2
    assert all(chunk.text for chunk in chunks)
    assert chunks[0].metadata["source_name"] == "demo.md"
    assert chunks[0].metadata["doc_type"] == "md"
    assert chunks[0].metadata["chunk_index"] == 0


def test_overlap_shares_boundary_characters() -> None:
    text = "abcdefghijklmnopqrstuvwxyz0123456789"
    chunks = chunk_document(_doc(text), chunk_size=10, chunk_overlap=4)
    assert len(chunks) >= 2
    # With size 10 and overlap 4, step is 6: second window starts at index 6.
    assert chunks[0].text.startswith("abcdefghij")
    assert chunks[1].text.startswith("ghijklmnop")


def test_invalid_chunk_size() -> None:
    try:
        validate_chunk_config(0, 0)
        assert False, "expected ChunkConfigError"
    except ChunkConfigError:
        pass


def test_invalid_overlap() -> None:
    try:
        validate_chunk_config(100, 100)
        assert False, "expected ChunkConfigError"
    except ChunkConfigError:
        pass


def test_deterministic_chunk_ids() -> None:
    first = make_chunk_id("/docs/a.md", 0, page_number=None)
    second = make_chunk_id("/docs/a.md", 0, page_number=None)
    third = make_chunk_id("/docs/a.md", 1, page_number=None)
    assert first == second
    assert first != third


def test_no_empty_chunks_from_whitespace_windows() -> None:
    text = "hello" + (" " * 40) + "world"
    chunks = chunk_document(_doc(text), chunk_size=20, chunk_overlap=5)
    assert all(chunk.text.strip() for chunk in chunks)
