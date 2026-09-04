# Day 1F — Understanding Python Dependencies

This guide explains the dependency concepts used in **production-rag-assistant**. The project is still early: a minimal FastAPI backend with `GET /health`. Day 1F focuses on understanding the packages that make that backend possible — not on adding RAG, AI, or new features.

---

## What is a dependency?

A **dependency** is software your project needs, but that you did not write yourself.

Your application code can call that software. Without it, parts of your project will not run.

Simple example from daily life: a recipe may depend on flour. You bring the recipe; you still need flour to cook. In software, your code is the recipe, and packages such as FastAPI are ingredients you install.

In this project, FastAPI and Uvicorn are dependencies of the backend.

---

## Is FastAPI part of Python?

**No.** FastAPI is **not** built into Python.

Python ships with a standard library (tools that come with Python itself). FastAPI is an **external Python package**. You must install it before your code can use it.

That is why `backend/app/main.py` can say:

```python
from fastapi import FastAPI
```

only after FastAPI has been installed into the environment. If FastAPI is missing, Python cannot import it, and the app will fail to start.

---

## What is requirements.txt?

`requirements.txt` is a text file that lists the Python packages a project needs.

In this repository, the backend list is:

```text
backend/requirements.txt
```

It currently includes:

```text
fastapi
uvicorn[standard]
```

Python projects use `requirements.txt` so another developer (or your future self) can install the same packages with one command.

Without that list, someone who clones the repository would have to guess which packages to install. With it, they can recreate a working setup more reliably.

---

## What does pip do?

**pip** is Python’s common tool for installing packages.

At a beginner level:

- Python is the language
- pip is the installer for Python packages
- packages live in places such as the Python Package Index (PyPI)

When you run a pip install command, pip downloads the package and installs it into the current Python environment (ideally your project’s virtual environment).

In this project, pip is how you install FastAPI and Uvicorn from `requirements.txt`.

---

## What does this command mean?

This is the command used to install the project’s listed packages:

```text
pip install -r requirements.txt
```

Broken into parts:

| Part | Meaning |
|------|---------|
| `pip` | The package installer |
| `install` | Tell pip to install something |
| `-r` | Read a list of packages from a file |
| `requirements.txt` | The file that contains the package list |

So the full command means:

**“Use pip to install every package listed in `requirements.txt`.”**

In this project, that installs FastAPI and Uvicorn so the local backend can run.

---

## Code vs Dependency

It helps to keep two ideas separate:

| | What it is | Example in this project |
|---|------------|-------------------------|
| **Our application code** | Files we write and own | `backend/app/main.py`, including the `health()` function |
| **External dependency** | Package someone else built; we install and use it | FastAPI |

Our code defines the health endpoint:

```python
@app.get("/health")
def health():
    return {"status": "ok", "service": "production-rag-assistant"}
```

That logic is ours. FastAPI is the external framework that:

- provides the `FastAPI` class
- registers the route with `@app.get("/health")`
- turns the returned dictionary into a JSON HTTP response

We write the endpoint. FastAPI is the dependency that makes that endpoint work as a web API.

Uvicorn is also a dependency: it runs the FastAPI application as a local server. Our health function does not replace Uvicorn; it depends on it to receive HTTP requests.

---

## What happens on another developer's computer?

Someone else can get the same minimal backend running with this sequence:

```text
clone repository
  -> create virtual environment
  -> install requirements
  -> run application
```

Step by step:

1. **Clone repository** — copy the project files to their computer
2. **Create virtual environment** — keep this project’s packages isolated
3. **Install requirements** — run `pip install -r requirements.txt` so FastAPI and Uvicorn are available
4. **Run application** — start the app with Uvicorn and call `GET /health`

If they skip installing requirements, their computer has the code but not the dependencies. The import of FastAPI will fail. The application code alone is not enough.

---

## Beginner Interview Questions

Exactly five questions based only on today’s dependency topic.

### 1. What is a dependency?

An external piece of software your project needs but did not write itself. In this project, FastAPI and Uvicorn are dependencies.

### 2. Is FastAPI included with Python?

No. FastAPI is an external package. It must be installed before the project can import and use it.

### 3. What is requirements.txt for?

It lists the packages needed to run the project so another developer can install them with one command and recreate a working setup.

### 4. What does `pip install -r requirements.txt` do?

It tells pip to install every package listed in `requirements.txt`. The `-r` flag means “read the package list from this file.”

### 5. What is the difference between application code and a dependency?

Application code is what we write, such as the `health()` endpoint in `backend/app/main.py`. A dependency is an installed package our code relies on, such as FastAPI.

---

## Key Takeaway

Remember this simple chain:

```text
our code
  -> needs packages (dependencies)
  -> listed in requirements.txt
  -> installed with pip
  -> then the app can run
```

In **production-rag-assistant**, we write the health endpoint. FastAPI and Uvicorn are the dependencies that make that endpoint runnable. `requirements.txt` is the shopping list; `pip` is how we buy the ingredients.
