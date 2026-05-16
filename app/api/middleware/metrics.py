import time
import re
from prometheus_client import Counter, Histogram, Gauge, Info, REGISTRY
from prometheus_client import values  # noqa: F401 — ensure process metrics load
from prometheus_client import gc_collector, platform_collector
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.config import settings

# ── Application Info Metric ───────────────────────────────────────────────────
# Single-value info metric for version/environment discovery in Grafana.
APP_INFO = Info(
    "autoheal_application",
    "AutoHeal DevOps Agent application metadata.",
)
APP_INFO.info(
    {
        "service": "autoheal-devops-agent",
        "environment": settings.environment,
        "python_version": "3.12",
    }
)

# ── Process & Runtime Collectors ──────────────────────────────────────────────
# Register standard collectors for CPU, memory, GC, and open FDs.
# These are available at /metrics automatically via prometheus_client defaults.
# Explicit registration guards against double-registration in test environments.
_registered = {c.__class__.__name__ for c in list(REGISTRY._names_to_collectors.values())}
if "GCCollector" not in _registered:
    gc_collector.GCCollector()
if "PlatformCollector" not in _registered:
    platform_collector.PlatformCollector()

# ── HTTP Metric Definitions ───────────────────────────────────────────────────

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests received.",
    ["method", "path", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "path"],
    # Production SLO-aligned buckets covering 10ms → 10s range
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

REQUESTS_INPROGRESS = Gauge(
    "http_requests_inprogress",
    "Number of HTTP requests currently being processed.",
    ["method", "path"],
)

ERROR_COUNT = Counter(
    "http_errors_total",
    "Total number of HTTP 5xx error responses.",
    ["method", "path", "status_code"],
)

# ── Cardinality-Safe Path Normalizer ─────────────────────────────────────────
# UUIDs, numeric IDs, and hashes in URL paths would create unbounded label
# cardinality in Prometheus. Normalize them to a fixed placeholder.
_PATH_PARAM_RE = re.compile(
    r"(?<=/)"  # must follow a slash
    r"(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"  # UUID
    r"|[0-9]+)"  # plain integer ID
    r"(?=/|$)"
)


def _normalize_path(path: str) -> str:
    """Replace dynamic path segments with {id} to prevent cardinality explosion."""
    return _PATH_PARAM_RE.sub("{id}", path)


# ── Middleware ────────────────────────────────────────────────────────────────


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Non-blocking ASGI middleware that instruments all HTTP requests.

    Path normalization prevents label cardinality explosion from dynamic routes.
    Designed for Chainguard distroless compatibility — no shell dependencies.
    Metrics are exposed at /metrics via prometheus_client.make_asgi_app().
    """

    async def dispatch(self, request: Request, call_next):
        method = request.method
        raw_path = request.url.path

        # Skip instrumentation for /metrics to avoid recursive cardinality noise
        if raw_path == "/metrics":
            return await call_next(request)

        path = _normalize_path(raw_path)

        REQUESTS_INPROGRESS.labels(method=method, path=path).inc()
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            REQUEST_COUNT.labels(method=method, path=path, status_code=500).inc()
            ERROR_COUNT.labels(method=method, path=path, status_code=500).inc()
            REQUESTS_INPROGRESS.labels(method=method, path=path).dec()
            raise

        duration = time.perf_counter() - start_time
        status_code = response.status_code

        REQUEST_COUNT.labels(method=method, path=path, status_code=status_code).inc()
        REQUEST_LATENCY.labels(method=method, path=path).observe(duration)
        REQUESTS_INPROGRESS.labels(method=method, path=path).dec()

        if status_code >= 500:
            ERROR_COUNT.labels(method=method, path=path, status_code=status_code).inc()

        return response
