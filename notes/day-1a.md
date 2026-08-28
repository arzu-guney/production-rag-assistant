# Day 1A Notes

**Date:** August 28, 2026  
**Repository:** [production-rag-assistant](https://github.com/) (cloned locally)

---

## Why I opened this repository

I cloned this repo today because I want a dedicated place to learn RAG properly — not just run someone else's demo once and forget how it worked.

Having a real GitHub repository helps me:

- Commit small steps as I go
- Keep notes next to the code (starting with this file)
- Build something I can point to and say "I made this, and I understand the pieces"

Right now the repo is almost empty on purpose. That is okay. Day 1A is about naming the goal and being clear about what does **not** exist yet.

## What I want to learn

- What happens **before** the LLM sees my question (ingestion, chunking, embedding, search)
- Why people use vector databases and what "similarity search" actually means
- How to tell if a RAG answer is good or hallucinated
- What extra work "production-style" systems add: logging, evals, error handling, security thinking
- How the pieces fit together without hiding behind a single magic library call

I am fine moving slowly. Understanding matters more than having a flashy demo on day one.

## What I think RAG means right now

My current mental model (beginner level, subject to change):

**RAG = retrieve relevant text, then generate an answer with that text as context.**

So the flow is roughly:

1. **Store** documents in a searchable form
2. **Retrieve** the bits that match the user's question
3. **Generate** an answer using an LLM plus those retrieved bits

I think the hard parts will be:

- Choosing good chunk sizes
- Getting retrieval right (wrong context → wrong or made-up answers)
- Measuring whether the system is actually helping

I have not used a vector database in my own project yet. I have seen the word "embedding" a lot but have not built the pipeline myself. That is why I am here.

## What I have not built yet

To be explicit — **none of this exists in the repository today:**

- No Python application code
- No FastAPI (or any API server)
- No frontend
- No document loaders or chunking logic
- No embeddings
- No vector database (Chroma, Pinecone, pgvector, etc.)
- No LangChain, LlamaIndex, or similar orchestration
- No LLM integration for question answering
- No tests
- No Docker or deployment configuration

What **does** exist:

- This GitHub repository (cloned locally)
- A `.gitignore` (standard Python template from GitHub)
- This README and Day 1A notes

That is it. This is **not** a RAG system yet. It is the start of a learning project, and that is exactly where I am supposed to be on Day 1A.
