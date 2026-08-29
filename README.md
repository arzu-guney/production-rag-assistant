# production-rag-assistant

A step-by-step learning project in **Applied AI Engineering**. The aim is to grow this into a production-style RAG assistant over time — understanding every decision along the way, not rushing through a tutorial.

## Project goal

Learn how Retrieval-Augmented Generation (RAG) works by building a small assistant that can answer questions using my own documents.

I want to move slowly enough to understand **why** each piece exists — ingestion, retrieval, generation, and later things like evaluation and observability — before adding the next layer.

This is a **learning project first**. The name refers to patterns I hope to practice later; it does **not** mean this repo is production-ready today.

## Why I am building this project

I am learning Applied AI Engineering and want a dedicated place to practice RAG from the ground up.

I opened this repository so I can:

- Take notes next to the code as I learn
- Commit small, understandable steps
- Build something real over time instead of only running one-off demos

## A very simple explanation of RAG

**RAG** stands for **Retrieval-Augmented Generation**.

In plain language:

1. You have documents (notes, PDFs, wiki pages, etc.).
2. When someone asks a question, the system **finds** useful pieces of text in those documents.
3. Those pieces are sent to a language model as **context**.
4. The model **generates** an answer using that context.

Simple analogy: **look up relevant notes first, then answer using those notes.**

A language model does not automatically know your private files. RAG is how you give it the right excerpts at question time.

## What I plan to build later

Nothing below exists in this repository yet. This is a rough roadmap as I learn:

- Document ingestion and chunking
- Embeddings and a vector store for search
- A retrieval step that fetches context for a question
- An LLM step that answers using that context
- A simple way to ask questions (API or UI)
- Basic evaluation and observability
- Security and safety experiments

I will add these pieces gradually, one decision at a time.

## Current Learning Focus

Day 1A is about getting the foundation right before any code. The focus is on repository setup, defining the project goal, and building a basic mental model of what RAG does. Application development has not started yet; that begins in later days once this mental model feels clear.

## Current status

| Item | Status |
|------|--------|
| GitHub repository | Created and cloned locally |
| Documentation | README and Day 1A notes |
| Application code | **None** |
| Working RAG application | **Does not exist yet** |

**There is no working RAG application in this repository yet.** Day 1A is repository setup, a clear README, and personal notes only.

See [`notes/day-1a.md`](notes/day-1a.md) for Day 1A reflections.
