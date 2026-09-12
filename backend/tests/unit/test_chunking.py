from pathlib import Path

from app.ingestion.chunking import (
    ChunkConfigError,
    chunk_document,
    make_chunk_id,
    validate_chunk_config,
)
from app.ingestion.loaders import LoadedDocument
from app.services.vector_store import VectorStore


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


def test_boundary_aware_splits_on_paragraph_boundaries() -> None:
    p1 = "First coherent paragraph with some useful introductory facts."
    p2 = "Second coherent paragraph explaining detailed system architecture."
    p3 = "Third coherent paragraph detailing operational deployment instructions."
    text = f"{p1}\n\n{p2}\n\n{p3}"

    # Target size fits p1 + p2 (~130 chars), but not all three (~200 chars)
    chunks = chunk_document(_doc(text), chunk_size=140, chunk_overlap=30)
    assert len(chunks) >= 2
    # Chunk 0 should end cleanly at paragraph boundary without severing words
    assert chunks[0].text.endswith("architecture.")
    # No chunk should start or end with broken partial words
    for chunk in chunks:
        words = chunk.text.split()
        assert words[0] in {"First", "Second", "Third", "coherent", "paragraph"}


def test_oversized_paragraph_splits_on_sentence_or_words() -> None:
    sentence1 = "Sentence one describes the problem clearly."
    sentence2 = "Sentence two provides the recommended solution."
    long_para = f"{sentence1} {sentence2}"

    # Chunk size fits sentence1 (~45 chars) but not both (~95 chars)
    chunks = chunk_document(_doc(long_para), chunk_size=55, chunk_overlap=15)
    assert len(chunks) >= 2
    # First chunk should break after sentence1 rather than cutting a word in half
    assert chunks[0].text.endswith("clearly.")
    assert not any(chunk.text.startswith("nce") or chunk.text.startswith("wo") for chunk in chunks)


def test_overlap_starts_on_clean_token_boundary() -> None:
    text = "The quick brown fox jumps over the lazy dog. Another quick brown fox appears."
    chunks = chunk_document(_doc(text), chunk_size=48, chunk_overlap=20)
    assert len(chunks) >= 2
    # Subsequent chunk should not start with a sliced fragment like "mps" or "azy"
    for chunk in chunks[1:]:
        first_word = chunk.text.split()[0]
        # Should be a complete word from the text
        assert first_word in text.split()


def test_vector_store_clear(tmp_path: Path) -> None:
    store = VectorStore(persist_path=tmp_path / "vs", collection_name="test_clear")
    assert store.count == 0
    store.upsert_chunks(
        ids=["chunk_1", "chunk_2"],
        documents=["text 1", "text 2"],
        embeddings=[[0.1] * 384, [0.2] * 384],
        metadatas=[{"source": "a.md"}, {"source": "b.md"}],
    )
    assert store.count == 2
    store.clear()
    assert store.count == 0
