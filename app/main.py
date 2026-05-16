from fastapi import FastAPI
from prometheus_client import make_asgi_app
from app.config import settings
from app.api.routes import health
from app.api.middleware.logging import LoggingMiddleware
from app.api.middleware.metrics import PrometheusMiddleware

app = FastAPI(
    title=settings.app_name,
    description="An AI-powered self-healing CI/CD pipeline",
    version="0.1.0",
)

# Middleware registration order matters — metrics first to capture total latency,
# then logging so request_id is available for structured log enrichment.
app.add_middleware(PrometheusMiddleware)
app.add_middleware(LoggingMiddleware)

app.include_router(health.router)

# Mount the Prometheus ASGI metrics exporter at /metrics.
# This is a separate ASGI app and is NOT routed through the middleware stack,
# which avoids recursive instrumentation of the metrics endpoint itself.
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
def read_root():
    return {"message": "Welcome to AutoHeal DevOps Agent API"}
