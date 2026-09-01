# Day 1B Notes

Day 1B is the first backend step in **production-rag-assistant**.

At this stage, the project has a tiny FastAPI server with one endpoint: `GET /health`. There is no RAG pipeline, no document search, and no AI features yet. This is intentional — we are learning the basics of how a backend works before adding more later.

---

## What is a backend?

The **backend** is the part of an application that runs on a server (or on your laptop during development) and does the work when something asks it to.

In **production-rag-assistant**, the backend lives in `backend/app/main.py`. Right now it does one simple job: answer when something asks, “Are you running?”

Think of it like this:

- **Backend** = the kitchen (does the work)
- **Client** = whoever asks for something (your browser, a script, or a future frontend)

On Day 1B, the backend is very small. That is normal. We are building the foundation first.

---

## What is an API endpoint?

An **API endpoint** is one specific address your backend listens on, combined with how you are allowed to call it.

It is made up of:

1. **HTTP method** — how you are asking (for example, `GET`)
2. **Path** — the URL path (for example, `/health`)

In this project, we have exactly one endpoint:

```
GET /health
```

That means: “Send a `GET` request to `/health`, and the backend will run the matching Python function.”

In `backend/app/main.py`, this line defines the endpoint:

```python
@app.get("/health")
```

Each endpoint is like a labeled door on the backend. Different doors can do different jobs later. For now, we only have one door.

---

## What is an HTTP GET request?

An **HTTP request** is how a client talks to a backend over the web.

A **GET** request is a type of HTTP request that means: *“Give me something”* or *“Let me check something.”*

You are not sending complex data to change things. You are mainly **reading** or **checking**.

Examples of GET in this project:

- Opening `http://127.0.0.1:8000/health` in a browser
- Running a command that asks the server for `/health`

For Day 1B, GET is the right choice for `/health` because we only want to **check** if the service is up — not upload files or submit questions.

---

## What should GET /health do?

The `/health` endpoint should answer one simple question:

**“Is the backend running and able to respond?”**

In **production-rag-assistant**, `GET /health` returns:

```json
{"status": "ok"}
```

That response means:

- The server process started successfully
- FastAPI received the request
- The backend handled the request and sent a reply

`/health` does **not** check RAG features, documents, or AI logic — because those do not exist in the project yet. It only checks that the basic backend plumbing works.

This is a common first endpoint in real projects too. Before building bigger features, you want proof that the server is alive.

---

## What happens when I call GET /health?

Here is the step-by-step flow for this project:

### 1. Request

You send:

```
GET /health
```

For example, by visiting `http://127.0.0.1:8000/health`.

### 2. FastAPI route

FastAPI receives the request and looks for a matching route:

- Method: `GET`
- Path: `/health`

It finds the route registered by:

```python
@app.get("/health")
```

### 3. Python function

FastAPI calls this function:

```python
def health():
    return {"status": "ok"}
```

### 4. Return value

The function returns a Python dictionary:

```python
{"status": "ok"}
```

FastAPI converts it to JSON for the HTTP response body.

### 5. HTTP response

You receive a response like:

- **Status code:** `200` (success)
- **Body:** `{"status": "ok"}`

### Full sequence

```text
GET /health
  → request arrives at the server
  → FastAPI matches the route @app.get("/health")
  → Python function health() runs
  → return value {"status": "ok"}
  → HTTP response sent back to you
```

---

## Where this project stands

**production-rag-assistant** is still at the very beginning.

What exists after Day 1B:

- A minimal FastAPI backend
- One health-check endpoint

What does **not** exist yet:

- RAG
- Document upload
- Search over documents
- Any AI or LLM integration

Day 1B is about understanding how a backend receives a request and sends back a response. That mental model will matter when we add real features later.
