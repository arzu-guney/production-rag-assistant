# Day 1B — Backend Basics

This guide explains the first backend step in **production-rag-assistant**.

At this stage, the project has a small FastAPI server with one endpoint: `GET /health`. There is no RAG pipeline, document search, or AI functionality yet. Day 1B is about learning how a backend receives a request and sends back a response.

---

## What is a backend?

A **backend** is the part of an application that runs on a machine and does work when something asks it to.

It listens for incoming requests, runs your code, and sends answers back.

In this project, the backend lives in `backend/app/main.py`. Right now it does one simple job: confirm that the server is running.

**Simple analogy:**

- **Backend** = the kitchen (does the work)
- **Client** = whoever asks for something (your browser, a script, or a tool)

Example in this project: when you open `http://127.0.0.1:8000/health`, your browser is the client, and the FastAPI app in `backend/app/main.py` is the backend.

---

## What is an API?

An **API** (Application Programming Interface) is a defined way for programs to talk to each other.

For a web backend, the API tells callers:

- **what** they can ask for
- **how** they should ask (HTTP method + URL)
- **what kind of answer** they will get back (often JSON)

**JSON** is a text format for structured data. It looks like a Python dictionary written as text.

In **production-rag-assistant**, the API is very small. It exposes one operation: check whether the service is alive. Other features may be added later, but they do not exist yet.

---

## What is an API endpoint?

An **API endpoint** is one specific entry point on a backend.

Each endpoint is defined by two parts:

1. **HTTP method** — how you are asking (for example, `GET`)
2. **Path** — the URL path (for example, `/health`)

Together, they identify one "door" on the backend.

In this project, there is exactly one endpoint:

```
GET /health
```

In code, it is registered here:

```python
@app.get("/health")
```

That line means: "When someone sends a `GET` request to `/health`, run the matching Python function."

---

## What is an HTTP GET request?

**HTTP** (Hypertext Transfer Protocol) is the language clients and servers use to communicate on the web.

An **HTTP request** is what the client sends. It includes:

- a **method** (such as `GET`)
- a **path** (such as `/health`)

A **GET** request means: *"Give me something"* or *"Let me check something."*

You are mainly **reading** or **checking**, not sending complex data to change the server.

Examples in this project:

- Opening `http://127.0.0.1:8000/health` in a browser
- Using a tool that asks the server for `/health`

`GET` is the right method for `/health` because we only want to check status, not upload files or submit questions.

---

## What is a health endpoint?

A **health endpoint** is a simple endpoint that answers one question:

**"Is this service running and able to respond?"**

It is often called `/health` and is one of the first endpoints added to a new backend.

In **production-rag-assistant**, the health endpoint confirms that:

- the server process started
- FastAPI is receiving requests
- the backend can return a response

It does **not** check RAG, documents, or AI features — because those are not part of the project yet. It only checks basic backend plumbing.

---

## What does GET /health mean?

`GET /health` is shorthand for an HTTP request with:

- **Method:** `GET`
- **Path:** `/health`

Read it as: *"Using GET, ask the `/health` endpoint for a status check."*

In this project, `GET /health` returns JSON like:

```json
{"status": "ok", "service": "production-rag-assistant"}
```

What each field means:

- `"status": "ok"` — the backend is responding
- `"service": "production-rag-assistant"` — which service answered

That is the entire API surface of the project at this early stage.

---

## What happens when GET /health is called?

Here is the full flow, step by step:

### 1. Client

You (or your browser) send a request to the running server.

Example: visit `http://127.0.0.1:8000/health`

### 2. GET /health

The request arrives as:

```
GET /health
```

### 3. FastAPI route

FastAPI looks at the method (`GET`) and path (`/health`), then finds the matching route:

```python
@app.get("/health")
```

### 4. Python function

FastAPI calls the `health()` function:

```python
def health():
    return {"status": "ok", "service": "production-rag-assistant"}
```

### 5. Python dictionary

The function returns a Python **dictionary** — a collection of key-value pairs:

```python
{"status": "ok", "service": "production-rag-assistant"}
```

### 6. JSON HTTP response

FastAPI converts that dictionary to **JSON** and sends it back as the HTTP response body, with status code `200` (success).

You see:

```json
{"status": "ok", "service": "production-rag-assistant"}
```

### Full sequence

```text
client
  → GET /health
  → FastAPI route
  → Python function
  → Python dictionary
  → JSON HTTP response
```

### Key takeaway

An API endpoint connects an **HTTP request** to **Python code**. You call `GET /health`, Python runs `health()`, and the return value becomes the response the client receives.

That pattern — request in, Python logic, response out — is the foundation every later feature in this project will build on.
