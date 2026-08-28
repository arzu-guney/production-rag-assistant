# production-rag-assistant

A learning project for building a production-style RAG assistant — step by step, from an empty repository to something real.

## Project goal

Learn how Retrieval-Augmented Generation (RAG) works by building a small but serious assistant: one that can answer questions using my own documents, with room later for evaluation, observability, and good engineering habits.

This is a **learning project first**. The name says "production" because I want to practice patterns used in real systems — not because this repo is production-ready today.

## Why I am building this

I want to go beyond copying a tutorial notebook and actually understand what happens when you ask an AI a question about your own files.

I am interested in:

- How documents get split, embedded, and stored
- How a system finds relevant context before calling an LLM
- What "good enough" looks like when you are learning, and what "production-style" might mean later (logging, testing, guardrails)

I opened this repository on **Day 1A** so I have a clear place to learn, take notes, and track progress over time.

## What RAG means (simple terms)

**RAG** stands for **Retrieval-Augmented Generation**.

In plain language:

1. You have a collection of documents (PDFs, notes, wiki pages, etc.).
2. When someone asks a question, the system **searches** those documents for useful pieces of text.
3. Those pieces are passed to a language model as **context**.
4. The model **generates** an answer based on that context — ideally grounded in your data, not only in what it memorized during training.

Think of it as: **look up relevant notes first, then answer using those notes.**

That is the core idea. Everything else — vector databases, chunking strategies, reranking, evals — builds on top of this pattern.

## What I plan to build later

Nothing below exists in this repo yet. This is the roadmap I have in mind as I learn:

- A way to ingest and chunk documents
- Embeddings and a vector store for semantic search
- A retrieval step that fetches relevant context for a question
- An LLM call that answers using that context
- A simple API or UI to ask questions
- Basic evaluation: "Did we retrieve the right stuff? Is the answer faithful?"
- Observability: logging, tracing, and debugging bad answers
- Security and safety experiments (e.g. prompt injection awareness, access control ideas)

I will add these pieces gradually. I am not rushing to install every framework on Day 1.

## Current status

| Item | Status |
|------|--------|
| GitHub repository | Created and cloned locally |
| Application code | **None yet** |
| Backend / API | Not started |
| Frontend | Not started |
| Embeddings / vector DB | Not started |
| Tests / Docker / deployment | Not started |

**Day 1A:** repository setup and learning notes only. This is **not** a working RAG system yet — it is the honest starting point of the project.

See [`notes/day-1a.md`](notes/day-1a.md) for today's reflections.
