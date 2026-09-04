# Backend Dependencies

This document explains the Python packages used by the current backend in **production-rag-assistant**.

The backend is still minimal. It exposes one endpoint:

```text
GET /health
```

That endpoint returns a simple JSON response so you can confirm the server is running. The packages below are only what is needed for that small FastAPI application.

---

## Current dependency file

The backend packages are listed in:

```text
backend/requirements.txt
```

This file is a plain-text shopping list of Python packages the backend needs. Another developer (or your future self) can install everything from that list instead of guessing package names.

Right now, `backend/requirements.txt` contains:

```text
fastapi
uvicorn[standard]
```

---

## Why dependencies matter

The application code in `backend/app/main.py` is not enough on its own.

That file imports FastAPI:

```python
from fastapi import FastAPI
```

If FastAPI is not installed on the machine, Python cannot import it, and the app will not start.

Dependencies matter because:

- Your computer and another developer’s computer do not share packages automatically
- Cloning the repository copies the code, not the installed packages
- Installing from `requirements.txt` recreates the same package setup

So before running the backend, the listed packages must be installed into the local Python environment (usually a virtual environment).

---

## Current backend packages

### FastAPI

**What it is:** FastAPI is an external Python web framework for building APIs.

**Why this project needs it:** The backend uses FastAPI to create the application object, register the `GET /health` route, and turn the Python return value into a JSON HTTP response.

Without FastAPI, the current health endpoint would not exist as a web API.

### Uvicorn

**What it is:** Uvicorn is a local server that runs FastAPI applications.

In `requirements.txt`, it appears as `uvicorn[standard]`. That means install Uvicorn plus a recommended set of extra helpers for a smoother local development experience. For beginners, it is enough to think of it as “Uvicorn with useful extras.”

**Why this project needs it:** FastAPI defines the API. Uvicorn is what starts the process, listens for HTTP requests, and passes them to FastAPI.

A common local command is:

```text
uvicorn app.main:app --reload
```

Without Uvicorn (or another similar server), the FastAPI code would be just a Python file and would not listen for requests such as `GET /health`.

---

## How dependencies are installed

From the `backend` folder, with a virtual environment activated, install the listed packages with:

```text
pip install -r requirements.txt
```

What the parts mean:

| Part | Meaning |
|------|---------|
| `pip` | Python’s package installer |
| `install` | Install packages |
| `-r` | Read the package list from a file |
| `requirements.txt` | The file that lists the packages |

This command installs every package named in `backend/requirements.txt` into the current environment.

After that, the backend can import FastAPI and run under Uvicorn.

---

## What this project does not use yet

The current `requirements.txt` is intentionally small. This project does **not** yet use:

- RAG
- Embeddings
- Vector databases
- LLM APIs
- Document upload
- Databases
- Authentication
- Frontend dependencies

Those may appear later as the learning project grows. They are not part of the backend today.

---

## Key Takeaway

`backend/requirements.txt` lists the packages needed to run the current FastAPI health endpoint. Installing that list with `pip install -r requirements.txt` makes it much easier to run the same backend on another machine.

```text
code alone  →  not enough
code + packages from requirements.txt  →  backend can run
```
