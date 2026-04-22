"""
AutoGST Pro + SmartTax AI — FastAPI Backend
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from jose import JWTError

from config.settings import settings
from config.database import Base, engine, check_db_connection
from config.logging_config import logger

from routes.auth import router as auth_router
from routes.transactions import router as txn_router
from routes.gst import router as gst_router
from routes.upload import router as upload_router
from routes.reports import router as reports_router
from routes.tax import router as tax_router
from routes.dashboard import dashboard_router, alerts_router
from routes.ai import router as ai_router

from utils.exceptions import (
    validation_exception_handler,
    sqlalchemy_exception_handler,
    jwt_exception_handler,
    generic_exception_handler,
    http_exception_handler,
)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs("logs", exist_ok=True)
os.makedirs("ml/models", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("=" * 60)
    logger.info("AutoGST Pro + SmartTax AI — Starting up")
    logger.info("Environment: %s", settings.APP_ENV)

    # Create DB tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error("Failed to create DB tables: %s", str(e))

    # Check DB connection
    if check_db_connection():
        logger.info("Database connection: OK")
    else:
        logger.warning("Database connection: FAILED — some features may not work")

    # Pre-load ML classifier
    try:
        from services.ml_service import get_classifier
        get_classifier()
        logger.info("ML classifier: loaded")
    except Exception as e:
        logger.warning("ML classifier load failed: %s", str(e))

    logger.info("Server ready at http://%s:%d", settings.APP_HOST, settings.APP_PORT)
    logger.info("API docs at http://%s:%d/docs", settings.APP_HOST, settings.APP_PORT)
    logger.info("=" * 60)

    yield

    logger.info("AutoGST Pro — Shutting down")


# ─── App Init ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AutoGST Pro + SmartTax AI",
    description="Production-ready GST management and tax calculation platform for Indian businesses",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── Middleware ───────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Exception Handlers ──────────────────────────────────────────────────────

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(JWTError, jwt_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ─── Routes ──────────────────────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(txn_router, prefix=API_PREFIX)
app.include_router(gst_router, prefix=API_PREFIX)
app.include_router(upload_router, prefix=API_PREFIX)
app.include_router(reports_router, prefix=API_PREFIX)
app.include_router(tax_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(alerts_router, prefix=API_PREFIX)
app.include_router(ai_router, prefix=API_PREFIX)


# ─── Health Check ────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health_check():
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "version": "1.0.0",
        "database": "connected" if db_ok else "disconnected",
        "environment": settings.APP_ENV,
    }


@app.get("/", tags=["System"])
def root():
    return {
        "app": "AutoGST Pro + SmartTax AI",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# ─── Dev Runner ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_ENV == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )
