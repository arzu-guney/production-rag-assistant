# Day 1E — Local Development Basics

This guide explains how to run the small FastAPI backend in **production-rag-assistant** on your own computer. The project is still at an early stage: one health endpoint, no RAG, and no AI features yet. Day 1E focuses on local development — the skills you need before adding more features later.

---

## What is local development?

**Local development** means building and running a project on **your own computer**, not on a public server on the internet.

When you develop locally:

- The code lives in a folder on your machine (this repository)
- You start the app yourself (for example with Uvicorn)
- You test it in your browser using a local address such as `http://127.0.0.1:8000`

You are not “deploying” the app for other people to use yet. You are learning, editing, and checking that things work in a safe place you control.

In **production-rag-assistant**, local development is how you run the FastAPI app in `backend/app/main.py` and call `GET /health` to see if it responds.

---

## What is a virtual environment?

A **virtual environment** is a private space on your computer for one Python project’s packages.

Python projects often need third-party libraries (such as FastAPI and Uvicorn). If you install every package into one global Python installation, projects can conflict with each other — different apps may need different versions of the same library.

A virtual environment helps by:

- Keeping this project’s packages **separate** from other projects
- Making it clearer which packages belong to **production-rag-assistant**
- Reducing “it works on my machine” problems caused by mixed versions

You create a virtual environment once for the project, activate it when you work, then install packages into it. The packages stay tied to this project instead of your whole system.

---

## What is requirements.txt?

`requirements.txt` is a text file that lists the **Python packages** this project needs.

In this repository, the backend list lives at:

```text
backend/requirements.txt
```

Right now it contains only what is needed for the minimal FastAPI app:

```text
fastapi
uvicorn[standard]
```

What that means:

- **fastapi** — the web framework that defines the API and endpoints
- **uvicorn[standard]** — the server that runs the FastAPI app locally

You use this file to install dependencies with a command such as:

```text
pip install -r requirements.txt
```

When someone new clones **production-rag-assistant**, `requirements.txt` tells them which packages to install so the health endpoint can run the same way on their machine.

---

## What is Uvicorn?

**Uvicorn** is a local **ASGI server**. In simple terms: it is the program that **runs** your FastAPI application and listens for HTTP requests.

FastAPI defines the routes (such as `GET /health`). Uvicorn is what starts the process, keeps it running, and passes incoming requests to FastAPI.

A common command from the `backend` folder looks like:

```text
uvicorn app.main:app --reload
```

What the pieces mean:

- `app.main` — the Python module `app/main.py`
- `:app` — the FastAPI object named `app` inside that file
- `--reload` — restart the server automatically when you change code (useful while learning)

Without Uvicorn (or another similar server), your FastAPI code would be just a Python file — it would not listen for HTTP requests on its own.

---

## What does 127.0.0.1 mean?

`127.0.0.1` is a special IP address that always means **this computer** — also called **localhost**.

When you open:

```text
http://127.0.0.1:8000/health
```

you are not calling a remote server on the internet. You are talking to the FastAPI app running **on your own machine**.

`localhost` is another name for the same idea. For local development in this project, `127.0.0.1` and `localhost` both refer to your computer.

---

## What does port 8000 mean?

A **port** is a numbered “door” on your computer where a program can listen for network connections.

Many apps can run on the same machine at the same time. Ports keep them separate:

- One app might listen on port `8000`
- Another might listen on port `3000`

In this project, Uvicorn commonly uses **port 8000**. That means the FastAPI backend is available at:

```text
http://127.0.0.1:8000
```

The full health URL becomes:

```text
http://127.0.0.1:8000/health
```

- `127.0.0.1` — your local machine
- `8000` — the port where Uvicorn is listening
- `/health` — the path of the endpoint

If nothing is running on port 8000, that URL will fail. The address only works while the local server is up.

---

## How does this connect to GET /health?

When the app is running locally, calling `/health` is how you send a request to the FastAPI backend.

The connection looks like this:

1. You start Uvicorn so the FastAPI app is listening on `127.0.0.1:8000`
2. You open `http://127.0.0.1:8000/health` (or call it with a tool)
3. That sends `GET /health` to your local backend
4. FastAPI matches the request to the `health()` function in `backend/app/main.py`
5. The function returns a dictionary, converted to JSON for the response

Example response:

```json
{"status": "ok", "service": "production-rag-assistant"}
```

Local development tools (`127.0.0.1`, port `8000`, Uvicorn) are the path that lets your browser reach the Python endpoint. Without the local server running, `/health` has nothing to talk to.

---

## Beginner Interview Questions

Exactly five questions based only on today’s local-development concepts.

### 1. What is local development?

Running and testing the project on your own computer before deploying it anywhere else. In this project, that means starting the FastAPI app locally and checking endpoints such as `/health`.

### 2. Why use a virtual environment?

To keep this project’s Python packages isolated from other projects, so dependency versions do not conflict and the environment stays easier to reproduce.

### 3. What is requirements.txt for?

It lists the Python packages needed to run the project. In **production-rag-assistant**, `backend/requirements.txt` currently lists FastAPI and Uvicorn.

### 4. What is the difference between FastAPI and Uvicorn?

FastAPI is the framework that defines the API and endpoints. Uvicorn is the server that runs the FastAPI app and listens for HTTP requests locally.

### 5. What do 127.0.0.1 and port 8000 mean together?

`127.0.0.1` means your local machine. Port `8000` is the door where the local server listens. Together they form the address of the running app, such as `http://127.0.0.1:8000/health`.

---

## Key Takeaway

Local development in **production-rag-assistant** works like this:

```text
your computer
  → virtual environment + packages from requirements.txt
  → Uvicorn runs the FastAPI app
  → listens on 127.0.0.1:8000
  → GET /health reaches the Python endpoint
  → JSON response returns to you
```

You write Python code, install the listed packages, start a local server, and talk to your own machine through a port. That is the foundation for every later feature — and for now, the only feature is a simple health check to prove the plumbing works.
