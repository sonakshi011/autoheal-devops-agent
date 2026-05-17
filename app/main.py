import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from prometheus_client import make_asgi_app

from app.config import settings
from app.api.routes import health
from app.api.routes.v1 import v1_router
from app.api.middleware.logging import LoggingMiddleware
from app.api.middleware.metrics import PrometheusMiddleware
from app.models.responses import APIErrorResponse

app = FastAPI(
    title=settings.app_name,
    description="An AI-powered self-healing CI/CD pipeline",
    version="0.1.0",
)

# ─── Centralized Exception Handling ───────────────────────────────────────────

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    error_resp = APIErrorResponse(error=str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        content=json.loads(error_resp.model_dump_json())
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_resp = APIErrorResponse(error=str(exc.errors()))
    return JSONResponse(
        status_code=422,
        content=json.loads(error_resp.model_dump_json())
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log details will still be recorded by LoggingMiddleware
    error_resp = APIErrorResponse(error="An internal server error occurred.")
    return JSONResponse(
        status_code=500,
        content=json.loads(error_resp.model_dump_json())
    )

# ─── Middleware ───────────────────────────────────────────────────────────────

# Dynamic Allowed Origins parsed from settings.allowed_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus and Logging
app.add_middleware(PrometheusMiddleware)
app.add_middleware(LoggingMiddleware)

# ─── Routes ───────────────────────────────────────────────────────────────────

app.include_router(health.router)
app.include_router(v1_router)

# Mount the Prometheus ASGI metrics exporter at /metrics.
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
def read_root():
    return {"message": "Welcome to AutoHeal DevOps Agent API"}
