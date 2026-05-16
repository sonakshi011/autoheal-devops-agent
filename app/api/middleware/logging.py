import time
import uuid
import logging
import traceback
from pythonjsonlogger.json import JsonFormatter
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.config import settings

# ── Structured JSON Formatter ─────────────────────────────────────────────────
# Single-line JSON output prevents multiline log corruption in Loki.
# Fields are stable across all log lines for consistent Loki label extraction.
_handler = logging.StreamHandler()
_handler.setFormatter(
    JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger_name"},
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
)

# ── Root Logger Configuration ─────────────────────────────────────────────────
# Replace all handlers globally to ensure single-line JSON on stdout.
# Suppresses uvicorn's default access logs to prevent duplicate entries.
logging.root.setLevel(logging.getLevelName(settings.log_level.upper()))
logging.root.handlers = [_handler]

# Silence uvicorn's own access logger — our middleware covers request logging
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

logger = logging.getLogger("autoheal.api")

# ── Static log context (injected into every log record via LoggingMiddleware) ─
_STATIC_CONTEXT = {
    "service_name": "autoheal-devops-agent",
    "environment": settings.environment,
}


class LoggingMiddleware(BaseHTTPMiddleware):
    """Emits a structured JSON log line for every HTTP request.

    Propagates or generates a request_id:
    - Reads X-Request-ID from incoming headers if present (distributed tracing).
    - Generates a UUID4 if absent.
    - Returns X-Request-ID in the response headers for client correlation.
    - Future OpenTelemetry trace_id can be injected alongside request_id here.

    All fields are designed for Loki label extraction and AI incident correlation.
    """

    async def dispatch(self, request: Request, call_next):
        # Propagate existing request ID or generate a new one
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        try:
            start_time = time.perf_counter()
            response = await call_next(request)
            latency_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "http_request",
                extra={
                    **_STATIC_CONTEXT,
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "latency_ms": round(latency_ms, 2),
                },
            )
        except Exception as exc:
            # Log the full traceback as a single structured field to prevent
            # Loki multiline ingestion corruption.
            logger.error(
                "http_request_exception",
                extra={
                    **_STATIC_CONTEXT,
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(exc),
                    "traceback": traceback.format_exc().replace("\n", "\\n"),
                },
            )
            raise

        # Inject request_id into response headers for client-side correlation
        response.headers["X-Request-ID"] = request_id
        return response
