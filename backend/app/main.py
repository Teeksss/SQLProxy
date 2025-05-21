"""
Main Application for SQL Proxy

This is the main entry point for the SQL Proxy application,
which sets up the FastAPI application, middleware, and routes.

Last updated: 2025-05-20 12:00:43
Updated by: Teeksss
"""

import logging
import time
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.api.api import api_router
from app.metrics.middleware import MetricsMiddleware
from app.security.middleware import SecurityMiddleware
from app.db.init_db import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.LOG_FILE)
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.OPENAPI_ENABLED else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add metrics middleware
app.add_middleware(MetricsMiddleware)

# Add security middleware
app.add_middleware(SecurityMiddleware)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/docs", include_in_schema=False)
async def get_swagger_documentation():
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=f"{settings.PROJECT_NAME} - Swagger UI",
        oauth2_redirect_url=f"{settings.API_V1_STR}/oauth2-redirect",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.15.5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.15.5/swagger-ui.css",
    )

@app.get("/redoc", include_in_schema=False)
async def get_redoc_documentation():
    return get_redoc_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=f"{settings.PROJECT_NAME} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )

@app.get("/api-schema", include_in_schema=False)
async def get_open_api_schema():
    return JSONResponse(
        get_openapi(
            title=settings.PROJECT_NAME,
            version=settings.VERSION,
            description=settings.PROJECT_DESCRIPTION,
            routes=app.routes,
        )
    )

@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.PROJECT_DESCRIPTION,
        "documentation": f"{settings.SERVER_HOST}/docs",
    }

@app.get("/health", include_in_schema=False)
async def health():
    return {
        "status": "ok",
        "version": settings.VERSION,
        "timestamp": time.time()
    }

def start():
    """Initialize the application on startup"""
    logger.info("Initializing application")
    
    try:
        # Initialize database
        init_db()
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
    
    logger.info("Application initialized successfully")

# Initialize application on startup
@app.on_event("startup")
async def startup_event():
    start()

# Son güncelleme: 2025-05-20 12:00:43
# Güncelleyen: Teeksss