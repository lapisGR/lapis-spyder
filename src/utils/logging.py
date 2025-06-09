"""Logging configuration and utilities."""

import logging
import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from src.config import settings


def setup_logging():
    """Set up logging configuration."""
    # Remove default handler
    logger.remove()
    
    # Console handler
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    logger.add(
        sys.stderr,
        format=console_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # File handler
    if settings.log_file_path:
        log_path = Path(settings.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        if settings.log_format == "json":
            file_format = (
                "{{\"time\": \"{time:YYYY-MM-DD HH:mm:ss}\", "
                "\"level\": \"{level}\", "
                "\"module\": \"{name}\", "
                "\"function\": \"{function}\", "
                "\"line\": {line}, "
                "\"message\": \"{message}\"}}"
            )
        else:
            file_format = (
                "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
                "{name}:{function}:{line} | {message}"
            )
        
        logger.add(
            log_path,
            format=file_format,
            level=settings.log_level,
            rotation=settings.log_max_size,
            retention=settings.log_backup_count,
            compression="gz",
            backtrace=True,
            diagnose=True,
        )
    
    # Error file handler
    if settings.log_file_path:
        error_log_path = log_path.parent / "error.log"
        logger.add(
            error_log_path,
            format=file_format,
            level="ERROR",
            rotation=settings.log_max_size,
            retention=settings.log_backup_count,
            compression="gz",
            backtrace=True,
            diagnose=True,
        )
    
    # Configure standard library logging
    class InterceptHandler(logging.Handler):
        """Intercept standard library logs and route to loguru."""
        
        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            
            # Find caller from where record originated
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            
            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )
    
    # Install interceptor for standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Disable some noisy loggers
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("uvicorn.error").disabled = True


def get_logger(name: Optional[str] = None):
    """Get logger instance."""
    if name:
        return logger.bind(name=name)
    return logger


# Request logging middleware
class LoggingMiddleware:
    """Middleware for request/response logging."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Log request
            method = scope["method"]
            path = scope["path"]
            query_string = scope.get("query_string", b"").decode()
            
            full_path = f"{path}?{query_string}" if query_string else path
            
            logger.info(
                f"Request started: {method} {full_path}",
                extra={
                    "method": method,
                    "path": path,
                    "query_string": query_string,
                    "client": scope.get("client", ["unknown", 0])[0],
                }
            )
            
            # Process request
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    status_code = message["status"]
                    logger.info(
                        f"Request completed: {method} {full_path} - {status_code}",
                        extra={
                            "method": method,
                            "path": path,
                            "status_code": status_code,
                        }
                    )
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)