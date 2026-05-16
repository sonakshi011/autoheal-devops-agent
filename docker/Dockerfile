# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /build

# Set environment variables for poetry/pip
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Harden: Upgrade OS packages to patch base-image CVEs
RUN apt-get update && apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Harden: Upgrade OS packages, clean up, and create non-root user
RUN apt-get update && apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/* && \
    addgroup --system appgroup && adduser --system --group appgroup

# Install dependencies from wheels
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/* 

# Copy application code
COPY app/ ./app/
COPY ai_engine/ ./ai_engine/
COPY prompts/ ./prompts/

# Switch to non-root user
USER appgroup

# Harden: Native Python health check (removes curl dependency)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
