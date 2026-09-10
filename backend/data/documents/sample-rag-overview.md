# Sample Knowledge Base for production-rag-assistant

This document is an original sample created for this learning repository.
It is used to demonstrate local document indexing for a RAG pipeline.

## What is RAG?

Retrieval-Augmented Generation (RAG) is a pattern where a system first retrieves
relevant text from a document collection and then uses that text as context for
a language model. The goal is to ground answers in your own documents instead of
relying only on the model's training data.

## Why chunking matters

Large documents are usually split into smaller chunks before embedding.
Chunk size controls how much text each vector represents.
Overlap keeps neighbouring chunks from losing important sentences that sit on a
boundary between two windows.

## Local embeddings in this project

This project uses a local Sentence Transformers model so embeddings can be created
without an external API key. The same embedding model must be used for documents
and for future user queries so both live in the same vector space.

## What a vector store keeps

A vector database stores:

1. the embedding vector for each chunk
2. the original chunk text
3. metadata such as source filename and page number

Metadata is especially useful later for citations, for example:
"Answer based on sample-rag-overview.md".

## Health and ask endpoints

The FastAPI backend currently exposes:

- GET /health for liveness checks
- POST /ask for grounded question answering

POST /ask retrieves relevant indexed chunks, sends them to Gemini as context, and returns an answer with source citations derived from retrieval metadata.

## Safety note

Do not place private or copyrighted documents in this sample folder for demos.
Use only content you are allowed to share.
