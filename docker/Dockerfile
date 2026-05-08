# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /build

# Set environment variables for poetry/pip
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Create non-root user
RUN addgroup --system appgroup && adduser --system --group appgroup

# Install dependencies from wheels
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application code
COPY app/ ./app/
COPY ai_engine/ ./ai_engine/
COPY prompts/ ./prompts/

# Switch to non-root user
USER appgroup

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health/ || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
