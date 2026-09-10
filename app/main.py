"""Main FastAPI Application Entry Point."""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.logging import logger
from app.db.session import SessionLocal
from app.ml.model_registry import get_model_registry


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan events."""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]...")

    # Verify database connectivity
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        logger.info("Database connection verified successfully.")
    except Exception as e:
        logger.warning(
            f"Database connectivity check failed on startup: {e}. "
            "Ensure migrations have been run using 'alembic upgrade head'."
        )

    # Initialize ML Model Registry
    registry = get_model_registry()
    if registry.is_loaded():
        logger.info(f"ML Model successfully loaded: version {registry.get_model_version()}")
    else:
        logger.warning(
            "ML Model artifact not found on startup. Using heuristic fallback until trained."
        )

    yield

    logger.info("Shutting down FinTrack API server...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Financial Transaction Monitoring & Fraud Detection Platform combining "
        "explainable deterministic risk rules with Isolation Forest anomaly detection."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming HTTP request method, path, and processing duration."""
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)")
    return response


# Include API v1 routes
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"], summary="System health and database check")
def health_check():
    """Health check endpoint reporting API status and database connectivity."""
    db_status = "healthy"
    db_latency_ms = 0.0

    try:
        t0 = time.time()
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        db_latency_ms = round((time.time() - t0) * 1000, 2)
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    registry = get_model_registry()

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": {
            "status": db_status,
            "latency_ms": db_latency_ms,
        },
        "ml_model": {
            "loaded": registry.is_loaded(),
            "version": registry.get_model_version(),
        },
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format validation errors cleanly without exposing internals."""
    errors = exc.errors()
    error_msgs = []
    for err in errors:
        loc = " -> ".join(str(loc_item) for loc_item in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        error_msgs.append(f"{loc}: {msg}")

    return JSONResponse(
        status_code=422,
        content={"detail": error_msgs[0] if len(error_msgs) == 1 else error_msgs},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all unhandled exception handler to prevent leaking stack traces."""
    logger.exception(f"Unhandled server exception on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )
