"""Main FastAPI application entry point."""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.database import init_db, check_db_connection
from src.database.mongodb import check_mongodb_connection
from src.database.redis import check_redis_connection
from src.utils.logging import setup_logging, get_logger, LoggingMiddleware
from src.auth.middleware import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RequestValidationMiddleware,
    AuditLogMiddleware
)

# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Lapis Spider application")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Check connections
    if not check_db_connection():
        logger.error("PostgreSQL connection failed")
        raise RuntimeError("Database connection failed")
    
    if not await check_mongodb_connection():
        logger.error("MongoDB connection failed")
        raise RuntimeError("MongoDB connection failed")
    
    if not check_redis_connection():
        logger.error("Redis connection failed")
        raise RuntimeError("Redis connection failed")
    
    logger.info("All database connections successful")
    
    yield
    
    logger.info("Shutting down Lapis Spider application")


# Create FastAPI app
app = FastAPI(
    title="Lapis Spider",
    description="Web crawler system with AI-powered content processing",
    version="0.1.0",
    docs_url="/docs" if settings.app_debug else None,
    redoc_url="/redoc" if settings.app_debug else None,
    lifespan=lifespan,
)

# Add middlewares
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.trusted_hosts if not settings.app_debug else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add security middlewares (order matters - most specific first)
app.add_middleware(AuditLogMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestValidationMiddleware, max_request_size=10 * 1024 * 1024)
app.add_middleware(
    RateLimitMiddleware, 
    calls_per_minute=settings.rate_limit_per_minute,
    calls_per_hour=settings.rate_limit_per_hour
)

# Add request logging middleware
app.add_middleware(LoggingMiddleware)


# Add request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests."""
    import uuid
    
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response


# Add timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        f"Unhandled exception in request {request_id}: {exc}",
        extra={"request_id": request_id, "path": request.url.path}
    )
    
    if settings.app_debug:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc),
                "traceback": traceback.format_exc(),
                "request_id": request_id,
            }
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": request_id,
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    checks = {
        "postgres": check_db_connection(),
        "mongodb": await check_mongodb_connection(),
        "redis": check_redis_connection(),
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": checks,
            "timestamp": time.time(),
            "version": "0.1.0",
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Lapis Spider API",
        "version": "0.1.0",
        "description": "Web crawler system with AI-powered content processing",
        "docs_url": "/docs" if settings.app_debug else None,
        "health_url": "/health",
        "environment": settings.app_env,
    }


# Include API routers
from src.api import auth, crawl, content, monitor
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(crawl.router, prefix="/crawl", tags=["Crawling"])
app.include_router(content.router, prefix="/content", tags=["Content"])
app.include_router(monitor.router, prefix="/monitor", tags=["Monitoring"])


# CLI interface
def cli():
    """Command line interface."""
    import click
    import uvicorn
    
    @click.group()
    def cli_group():
        """Lapis Spider CLI."""
        pass
    
    @cli_group.command()
    @click.option("--host", default="0.0.0.0", help="Host to bind to")
    @click.option("--port", default=8000, help="Port to bind to")
    @click.option("--reload", is_flag=True, help="Enable auto-reload")
    def serve(host, port, reload):
        """Start the API server."""
        uvicorn.run(
            "src.main:app",
            host=host,
            port=port,
            reload=reload,
            log_config=None,  # Use our custom logging
        )
    
    @cli_group.command()
    def init_db_cmd():
        """Initialize the database."""
        init_db()
        click.echo("Database initialized successfully")
    
    @cli_group.command()
    def check_health():
        """Check system health."""
        import asyncio
        
        async def check():
            health = await health_check()
            click.echo(f"Health status: {health}")
        
        asyncio.run(check())
    
    cli_group()


if __name__ == "__main__":
    cli()