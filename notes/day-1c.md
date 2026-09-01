# Day 1C Notes

Day 1C is a small change to the existing backend in **production-rag-assistant**. No new endpoints were added. The goal is to see how a tiny change in Python code changes what the client receives back.

---

## What changed today?

The `GET /health` endpoint response was updated.

**Before:**

```json
{"status": "ok"}
```

**After:**

```json
{"status": "ok", "service": "production-rag-assistant"}
```

The endpoint now returns one extra field: `"service": "production-rag-assistant"`. This tells the caller which service answered the request.

That is the only change made on Day 1C.

---

## What did not change?

Several important things stayed the same:

- **The route** — still `/health`
- **The HTTP method** — still `GET`
- **The endpoint** — still one health-check endpoint at `GET /health`
- **The backend structure** — still a minimal FastAPI app in `backend/app/main.py`
- **The purpose** — still checking that the backend is running and responding

You are still calling the same door on the same backend. Only the answer coming back through that door changed slightly.

---

## Why did the HTTP response change?

The HTTP response changed because the **Python dictionary** returned by the `health` function changed.

In `backend/app/main.py`, the function used to return:

```python
{"status": "ok"}
```

It now returns:

```python
{"status": "ok", "service": "production-rag-assistant"}
```

FastAPI takes whatever dictionary the function returns and turns it into a **JSON** HTTP response body.

So:

- Change the Python return value → change the JSON the client sees

You did not change how HTTP works. You changed what your Python code gives back, and FastAPI passed that through automatically.

---

## Request to Response Flow

Here is what happens when you call `GET /health` in this project:

### 1. The client sends GET /health

You (or your browser) send an HTTP request:

- Method: `GET`
- Path: `/health`

Example: `http://127.0.0.1:8000/health`

### 2. FastAPI matches the request to the /health route

FastAPI looks at the method and path, then finds the route registered with:

```python
@app.get("/health")
```

### 3. The Python function for that route runs

FastAPI calls the `health()` function in `backend/app/main.py`.

### 4. The function returns a dictionary

The function runs and returns:

```python
{"status": "ok", "service": "production-rag-assistant"}
```

### 5. FastAPI converts the dictionary into a JSON response

FastAPI sends back an HTTP response with:

- Status code: `200` (success)
- Body: `{"status": "ok", "service": "production-rag-assistant"}`

### Simple view

```text
GET /health
  → FastAPI finds the /health route
  → health() runs
  → returns a dictionary
  → client receives JSON
```

---

## Key lesson

An **API endpoint** is a connection between an **HTTP request** and **Python code**.

- The **HTTP side** is what the client sends: `GET /health`
- The **Python side** is what your function does: run logic and return a value
- FastAPI sits in the middle and connects them

On Day 1C, you learned that this connection is easy to adjust. Change the Python return value, and the API response changes — without renaming the route or adding a new endpoint.

That is a useful pattern to remember as **production-rag-assistant** grows later. For now, the project is still at the very beginning: a small backend with one health-check endpoint, and no RAG or AI features yet.
