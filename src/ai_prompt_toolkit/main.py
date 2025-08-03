"""
Main FastAPI application for AI Prompt Toolkit.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from ai_prompt_toolkit.core.config import settings
from ai_prompt_toolkit.api.routes import api_router
from ai_prompt_toolkit.core.logging import setup_logging
from ai_prompt_toolkit.core.database import init_db
from ai_prompt_toolkit.core.exceptions import AIPromptToolkitException


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    setup_logging()
    logger = structlog.get_logger()
    
    logger.info("Starting AI Prompt Toolkit", version=settings.version)
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize LLM providers
    from ai_prompt_toolkit.services.llm_factory import LLMFactory
    llm_factory = LLMFactory()
    await llm_factory.initialize()
    logger.info("LLM providers initialized", providers=settings.get_enabled_providers())
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Prompt Toolkit")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title=settings.app_name,
        description="Advanced AI Prompt Engineering & Management Toolkit with automated optimization, injection detection, and multi-LLM support",
        version=settings.version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure appropriately for production
    )
    
    # Add Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    # Global exception handler
    @app.exception_handler(AIPromptToolkitException)
    async def ai_prompt_toolkit_exception_handler(request: Request, exc: AIPromptToolkitException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": settings.version,
            "providers": settings.get_enabled_providers()
        }
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "ai_prompt_toolkit.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
