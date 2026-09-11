# Production-oriented API image for production-rag-assistant.
# Uses the project's supported runtime: Python 3.11.
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install dependencies first for better Docker layer caching.
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Application code + sample knowledge documents only.
# Do not copy .env, .venv, or local Chroma data into the image.
COPY app ./app
COPY data/documents ./data/documents
COPY .env.example ./.env.example

EXPOSE 8000

# Lightweight health check using the Python stdlib (no extra packages).
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

# Production-style process: no --reload (reload is for local development only).
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
