# Day 1G — Understanding Python Imports

This guide explains one important line from the current backend in **production-rag-assistant**:

```python
from fastapi import FastAPI
```

The project is still early. It has a minimal FastAPI backend with `GET /health`. Day 1G focuses only on understanding how Python imports work — not on adding RAG, AI, or new features.

---

## What is an import in Python?

An **import** tells Python: “I want to use code that lives somewhere else.”

Python programs are often built from pieces:

- code you write yourself
- packages installed into your environment

An import connects those pieces. Instead of rewriting everything, you bring in tools that already exist.

In this project, `backend/app/main.py` imports `FastAPI` so the health endpoint can use the FastAPI framework.

Without imports, every program would have to reinvent basic building blocks.

---

## What does `from fastapi import FastAPI` mean?

Here is the same line broken into parts:

```python
from fastapi import FastAPI
```

| Part | Meaning |
|------|---------|
| `from` | Start from a specific package or module |
| `fastapi` | The package name to look in |
| `import` | Bring something into this file |
| `FastAPI` | The specific class we want to use |

Read it in plain English:

**“From the `fastapi` package, import the `FastAPI` class.”**

After this line runs successfully, the name `FastAPI` is available in `main.py`, so the next line can create the app:

```python
app = FastAPI()
```

---

## Where does `fastapi` come from?

`fastapi` is not built into Python. It comes from the **FastAPI package** installed into the active environment.

The connection is simple:

1. FastAPI is listed in `backend/requirements.txt`
2. You install it with `pip install -r requirements.txt`
3. After that, Python can find the `fastapi` package
4. Then `from fastapi import FastAPI` can succeed

So:

- `requirements.txt` says the project needs FastAPI
- `pip` installs FastAPI
- `import` uses FastAPI in your code

Installing comes first. Importing comes second.

---

## `pip install` vs `import`

These two lines look related, but they do different jobs.

### Installing

```text
pip install -r requirements.txt
```

This happens **outside** your application file. It downloads and installs packages into the environment.

Think of it as: **putting the toolbox on the shelf.**

### Importing

```python
from fastapi import FastAPI
```

This happens **inside** your Python code. It asks Python to load a package that is already installed.

Think of it as: **taking a tool out of the toolbox to use it.**

| Action | When | Purpose |
|--------|------|---------|
| `pip install ...` | Setup step | Make the package available in the environment |
| `import ...` | Inside Python code | Use the package in this file |

If the toolbox is empty, you cannot take a tool out of it. If FastAPI is not installed, the import cannot succeed.

---

## What happens if FastAPI is not installed?

If FastAPI is missing from the active environment, Python cannot find the `fastapi` package.

Then this line fails:

```python
from fastapi import FastAPI
```

At a beginner level, that usually appears as an **import error**: Python is saying, “You asked for `fastapi`, but I cannot find it here.”

Common reasons:

- packages were never installed
- the virtual environment is not activated
- you are using a different Python environment than the one where FastAPI was installed

The code file can still exist. The import fails because the dependency is not available in the environment Python is currently using.

---

## How does this connect to our current backend?

For the existing health endpoint, the sequence is:

```text
FastAPI is listed as a dependency
  -> pip installs FastAPI
  -> main.py imports FastAPI
  -> our application can use FastAPI
  -> FastAPI handles the existing GET /health route
```

In `backend/app/main.py`, after the import:

1. `app = FastAPI()` creates the application
2. `@app.get("/health")` registers the health route
3. `health()` returns the JSON response

Day 1G does not add any new functionality. It only explains how the import makes the current backend possible.

---

## Tiny Python Example

Here is a small generic example, separate from the application code, to show the idea of importing:

```python
from math import sqrt

print(sqrt(16))
# 4.0
```

What this means:

- `math` is a module
- `sqrt` is one function from that module
- the import brings `sqrt` into this file so you can call it

This is the same pattern as:

```python
from fastapi import FastAPI
```

Different package, same idea: bring in a name so you can use it.

---

## Beginner Interview Questions

Exactly five questions based only on today’s import topic.

### 1. What is an import?

An import tells Python to load code from another package or module so the current file can use it.

### 2. What is the difference between installing and importing a package?

Installing puts the package into the environment (for example with `pip`). Importing loads that installed package into your Python file so you can use it in code.

### 3. What does `from fastapi import FastAPI` do?

It loads the `FastAPI` class from the `fastapi` package into the current file so the application can create a FastAPI app.

### 4. Where does the `fastapi` package come from in this project?

It is listed in `backend/requirements.txt` and installed with `pip install -r requirements.txt`. After that, Python can import it.

### 5. What happens if FastAPI is not installed?

Python cannot find the package, so `from fastapi import FastAPI` fails with an import error, and the backend cannot start.

---

## Key Takeaway

Remember this short chain:

```text
install the package
  -> then import it
  -> then use it in your code
```

For this project:

```text
requirements.txt lists FastAPI
  -> pip installs FastAPI
  -> main.py runs: from fastapi import FastAPI
  -> the GET /health endpoint can work
```

`pip` puts the tool on the shelf. `import` picks it up. Both steps are needed.
