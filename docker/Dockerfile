# Stage 1: Builder
FROM cgr.dev/chainguard/python:latest-dev AS builder

WORKDIR /app

# Ensure bytecodes aren't written and output is unbuffered
ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a virtual environment for deterministic dependency isolation
# This is crucial because the runtime image lacks pip or any package manager
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install dependencies into the virtual environment
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime (Distroless)
FROM cgr.dev/chainguard/python:latest AS runtime

WORKDIR /app

# Set Python environment variables and ensure the venv is on the PATH
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/app/venv/bin:$PATH"

# Copy the completely isolated virtual environment from the builder
COPY --from=builder /app/venv /app/venv

# Copy application code
COPY app/ ./app/
COPY ai_engine/ ./ai_engine/
COPY prompts/ ./prompts/

# Security Note: The runtime image natively runs as `nonroot` (UID 65532).
# No chown, adduser, or user switching is required. The COPY command
# natively inherits the nonroot ownership from the builder stage.

# Shell-less Native Python health check
# Distroless images do NOT have /bin/sh. We must use the JSON array exec format.
# Python's urllib will throw an exception and exit 1 if the HTTP request fails.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["/app/venv/bin/python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')"]

EXPOSE 8000

# Clear the default entrypoint ('python') to prevent double-execution
ENTRYPOINT []

# Exec format mandatory for distroless (no shell evaluation)
CMD ["/app/venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
