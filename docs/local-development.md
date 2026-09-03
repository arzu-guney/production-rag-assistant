# Local Development Guide

This guide explains how to run the current FastAPI backend in **production-rag-assistant** on your own computer. It is written for beginners using **Windows Command Prompt**.

---

## Current project status

This project currently has a **minimal FastAPI backend** with one endpoint:

```text
GET /health
```

That endpoint returns a simple JSON response so you can confirm the server is running.

The following have **not** been implemented yet:

- RAG
- Document upload
- Embeddings
- Vector database
- LLM integration

You are only setting up and testing the small health-check backend.

---

## Prerequisites

Before you start, make sure you have:

- **Python** installed
- **Git** installed
- This **repository cloned locally** on your computer

This guide assumes you already have those ready. It does not cover installing them.

---

## Step 1: Open the project folder

Open **Command Prompt**, then move into your local copy of the repository.

Use your real path instead of the placeholder:

```text
cd path\to\production-rag-assistant
```

Example shape of a path:

```text
cd C:\Users\YourName\production-rag-assistant
```

---

## Step 2: Go to the backend folder

The FastAPI app and its dependency list live inside `backend`:

```text
cd backend
```

Your current folder should now be something like:

```text
...\production-rag-assistant\backend
```

---

## Step 3: Create a virtual environment

A virtual environment keeps this project’s Python packages separate from other projects.

From the `backend` folder, run:

```text
python -m venv .venv
```

This creates a folder named `.venv` inside `backend`.

---

## Step 4: Activate the virtual environment

Still in the `backend` folder, activate it with this **Windows Command Prompt** command:

```text
.venv\Scripts\activate
```

After activation, your prompt often shows `(.venv)` at the start. That means the virtual environment is active.

---

## Step 5: Install dependencies

Install the packages listed in `requirements.txt`:

```text
pip install -r requirements.txt
```

For this project, that installs the packages needed to run the minimal FastAPI app (including FastAPI and Uvicorn).

---

## Step 6: Run the FastAPI app

Start the local server:

```text
uvicorn app.main:app --reload
```

What this means:

- `app.main` — the file `app\main.py`
- `:app` — the FastAPI object named `app` in that file
- `--reload` — restart automatically when you change code

Leave this Command Prompt window open while the server is running. You should see output that Uvicorn is listening, usually on port `8000`.

---

## Step 7: Test the health endpoint

Open a browser and visit:

```text
http://127.0.0.1:8000/health
```

Or keep the server running and use another Command Prompt window if you prefer another tool — the important part is that the request goes to that URL.

The expected response should look like:

```json
{
  "status": "ok",
  "service": "production-rag-assistant"
}
```

If you see that, your local backend is running and the health endpoint is working.

---

## Troubleshooting

### Command not recognized

If you see a message that `python`, `pip`, or `uvicorn` is not recognized:

- Confirm Python is installed and available in Command Prompt
- Make sure the virtual environment is **activated** before using `pip` or `uvicorn`
- Close and reopen Command Prompt, then activate `.venv` again and retry

### Wrong folder

Many commands fail if you are not in the right directory.

Check that you are in the `backend` folder when you:

- create the virtual environment
- activate `.venv`
- run `pip install -r requirements.txt`
- run `uvicorn app.main:app --reload`

You can print the current folder with:

```text
cd
```

### Server not running

If the browser cannot open `/health`:

- Confirm Uvicorn is still running in Command Prompt
- Confirm you did not close the window that started the server
- Confirm the URL is exactly `http://127.0.0.1:8000/health`

The health endpoint only works while the local server is running.

### Port already in use

If Uvicorn says port `8000` is already in use:

- Another program (or an earlier Uvicorn process) may already be using port `8000`
- Stop the other process, or close the old Command Prompt window that started the server
- Then run `uvicorn app.main:app --reload` again

---

## Quick checklist

1. Open the project folder
2. `cd backend`
3. `python -m venv .venv`
4. `.venv\Scripts\activate`
5. `pip install -r requirements.txt`
6. `uvicorn app.main:app --reload`
7. Visit `http://127.0.0.1:8000/health`

That is enough to run the current backend locally. No RAG or AI features are included at this stage — only a working health check.
