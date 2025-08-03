"""
Template management API endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ai_prompt_toolkit.core.database import get_db
from ai_prompt_toolkit.models.prompt_template import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    TemplateSearchRequest,
    TemplateRenderRequest,
    TemplateRenderResponse,
    PromptTemplateRating,
    TemplateCategory
)
from ai_prompt_toolkit.services.template_service import template_service
from ai_prompt_toolkit.security.injection_detector import injection_detector

router = APIRouter()


@router.post("/", response_model=PromptTemplateResponse)
async def create_template(
    template: PromptTemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new prompt template."""
    # Validate template for injection attacks
    injection_detector.validate_prompt(template.template)
    
    return await template_service.create_template(db, template)


@router.get("/{template_id}", response_model=PromptTemplateResponse)
async def get_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Get a template by ID."""
    return await template_service.get_template(db, template_id)


@router.put("/{template_id}", response_model=PromptTemplateResponse)
async def update_template(
    template_id: str,
    template: PromptTemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing template."""
    # Validate template for injection attacks if template is being updated
    if template.template:
        injection_detector.validate_prompt(template.template)
    
    return await template_service.update_template(db, template_id, template)


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Delete a template."""
    success = await template_service.delete_template(db, template_id)
    return {"success": success}


@router.post("/search", response_model=List[PromptTemplateResponse])
async def search_templates(
    search_request: TemplateSearchRequest,
    db: Session = Depends(get_db)
):
    """Search templates based on criteria."""
    return await template_service.search_templates(db, search_request)


@router.get("/", response_model=List[PromptTemplateResponse])
async def list_templates(
    category: TemplateCategory = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List templates with optional filtering."""
    search_request = TemplateSearchRequest(
        category=category,
        limit=limit,
        offset=offset
    )
    return await template_service.search_templates(db, search_request)


@router.post("/render", response_model=TemplateRenderResponse)
async def render_template(
    render_request: TemplateRenderRequest,
    db: Session = Depends(get_db)
):
    """Render a template with provided variables."""
    rendered_prompt = await template_service.render_template(
        db,
        render_request.template_id,
        render_request.variables
    )
    
    return TemplateRenderResponse(
        rendered_prompt=rendered_prompt,
        template_id=render_request.template_id,
        variables_used=render_request.variables
    )


@router.post("/{template_id}/rate", response_model=PromptTemplateResponse)
async def rate_template(
    template_id: str,
    rating: PromptTemplateRating,
    db: Session = Depends(get_db)
):
    """Rate a template."""
    return await template_service.rate_template(db, template_id, rating.rating)


@router.get("/categories/list")
async def list_categories():
    """Get list of available template categories."""
    return {
        "categories": [
            {
                "value": category.value,
                "label": category.value.replace("_", " ").title()
            }
            for category in TemplateCategory
        ]
    }
