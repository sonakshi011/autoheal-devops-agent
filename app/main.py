from fastapi import FastAPI
from app.config import settings
from app.api.routes import health
from app.api.middleware.logging import LoggingMiddleware

app = FastAPI(
    title=settings.app_name,
    description="An AI-powered self-healing CI/CD pipeline",
    version="0.1.0",
)

app.add_middleware(LoggingMiddleware)
app.include_router(health.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to AutoHeal DevOps Agent API"}
