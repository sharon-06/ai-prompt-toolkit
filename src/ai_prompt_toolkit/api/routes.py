"""
Main API routes for AI Prompt Toolkit.
"""

from fastapi import APIRouter

from ai_prompt_toolkit.api.endpoints import (
    templates,
    optimization,
    security,
    llm,
    analytics
)

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    templates.router,
    prefix="/templates",
    tags=["templates"]
)

api_router.include_router(
    optimization.router,
    prefix="/optimization",
    tags=["optimization"]
)

api_router.include_router(
    security.router,
    prefix="/security",
    tags=["security"]
)

api_router.include_router(
    llm.router,
    prefix="/llm",
    tags=["llm"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"]
)
