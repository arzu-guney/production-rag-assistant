# Local data directories

## `documents/`

Place knowledge-base files here for indexing (`.txt`, `.md`, `.pdf`).

- Intended sample knowledge file: `documents/sample-rag-overview.md`
- Files named `README.md` inside `documents/` are **not** indexed (repository guidance, not knowledge)

Index from the `backend/` directory:

```text
python -m app.ingestion.indexer --path data/documents
```

## `vector_store/`

Created at runtime by ChromaDB. Gitignored. Do not commit this folder.

If you previously indexed a documents README by mistake, delete `vector_store/` once and run the indexer again so the collection only contains knowledge chunks.
