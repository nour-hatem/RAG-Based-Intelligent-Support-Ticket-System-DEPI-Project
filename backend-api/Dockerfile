# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Stage 1: builder — install dependencies into a clean layer
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /app

# System deps needed for some Python packages (e.g. faiss-cpu, scipy)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend-api/requirements.txt .

# Install torch CPU-only wheel first to avoid pulling the much larger CUDA build,
# then install the rest of the requirements against the already-installed torch.
RUN pip install --no-cache-dir \
        torch==2.12.1 \
        --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt


# ---------------------------------------------------------------------------
# Stage 2: runtime — lean final image
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

WORKDIR /app

# libgomp1 is required at runtime by faiss-cpu
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source only.
# data/, embeddings/, faiss/ are NOT copied — they are mounted as volumes at runtime.
COPY src/ ./src/
COPY backend-api/api/ ./api/
COPY backend-api/main.py ./main.py

# Port the app listens on (matches settings default + docker-compose)
EXPOSE 8000

# Run uvicorn. HOST and PORT are set via env (docker-compose / .env).
CMD ["sh", "-c", "uvicorn main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000}"]
