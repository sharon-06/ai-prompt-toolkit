"""
Service for managing prompt templates.
"""

from typing import List, Optional, Dict, Any
from uuid import uuid4
import structlog
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from jinja2 import Template, Environment, meta

from ai_prompt_toolkit.models.prompt_template import (
    PromptTemplateDB,
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    TemplateSearchRequest,
    TemplateCategory
)
from ai_prompt_toolkit.core.exceptions import TemplateNotFoundError, ValidationError


class TemplateService:
    """Service for managing prompt templates."""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.jinja_env = Environment()
    
    async def create_template(
        self,
        db: Session,
        template_data: PromptTemplateCreate
    ) -> PromptTemplateResponse:
        """Create a new prompt template."""
        
        # Validate template syntax
        try:
            template = Template(template_data.template)
            # Extract variables from template
            ast = self.jinja_env.parse(template_data.template)
            template_vars = meta.find_undeclared_variables(ast)
            
            # Update variables list if not provided
            if not template_data.variables:
                template_data.variables = list(template_vars)
            
        except Exception as e:
            raise ValidationError(f"Invalid template syntax: {str(e)}", "template")
        
        # Create database record
        db_template = PromptTemplateDB(
            id=str(uuid4()),
            **template_data.dict()
        )
        
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        
        self.logger.info("Template created", template_id=db_template.id, name=db_template.name)
        
        return PromptTemplateResponse.from_orm(db_template)
    
    async def get_template(self, db: Session, template_id: str) -> PromptTemplateResponse:
        """Get a template by ID."""
        
        db_template = db.query(PromptTemplateDB).filter(
            PromptTemplateDB.id == template_id
        ).first()
        
        if not db_template:
            raise TemplateNotFoundError(template_id)
        
        return PromptTemplateResponse.from_orm(db_template)
    
    async def update_template(
        self,
        db: Session,
        template_id: str,
        template_data: PromptTemplateUpdate
    ) -> PromptTemplateResponse:
        """Update an existing template."""
        
        db_template = db.query(PromptTemplateDB).filter(
            PromptTemplateDB.id == template_id
        ).first()
        
        if not db_template:
            raise TemplateNotFoundError(template_id)
        
        # Validate template syntax if template is being updated
        if template_data.template:
            try:
                Template(template_data.template)
                ast = self.jinja_env.parse(template_data.template)
                template_vars = meta.find_undeclared_variables(ast)
                
                # Update variables if not explicitly provided
                if template_data.variables is None:
                    template_data.variables = list(template_vars)
                    
            except Exception as e:
                raise ValidationError(f"Invalid template syntax: {str(e)}", "template")
        
        # Update fields
        update_data = template_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_template, field, value)
        
        db.commit()
        db.refresh(db_template)
        
        self.logger.info("Template updated", template_id=template_id)
        
        return PromptTemplateResponse.from_orm(db_template)
    
    async def delete_template(self, db: Session, template_id: str) -> bool:
        """Delete a template."""
        
        db_template = db.query(PromptTemplateDB).filter(
            PromptTemplateDB.id == template_id
        ).first()
        
        if not db_template:
            raise TemplateNotFoundError(template_id)
        
        db.delete(db_template)
        db.commit()
        
        self.logger.info("Template deleted", template_id=template_id)
        
        return True
    
    async def search_templates(
        self,
        db: Session,
        search_request: TemplateSearchRequest
    ) -> List[PromptTemplateResponse]:
        """Search templates based on criteria."""
        
        query = db.query(PromptTemplateDB)
        
        # Apply filters
        if search_request.query:
            query = query.filter(
                or_(
                    PromptTemplateDB.name.ilike(f"%{search_request.query}%"),
                    PromptTemplateDB.description.ilike(f"%{search_request.query}%"),
                    PromptTemplateDB.template.ilike(f"%{search_request.query}%")
                )
            )
        
        if search_request.category:
            query = query.filter(PromptTemplateDB.category == search_request.category.value)
        
        if search_request.tags:
            # Filter by tags (assuming JSON contains array)
            for tag in search_request.tags:
                query = query.filter(PromptTemplateDB.tags.contains([tag]))
        
        if search_request.author:
            query = query.filter(PromptTemplateDB.author == search_request.author)
        
        if search_request.is_public is not None:
            query = query.filter(PromptTemplateDB.is_public == search_request.is_public)
        
        if search_request.min_rating:
            query = query.filter(PromptTemplateDB.rating >= search_request.min_rating)
        
        # Apply sorting
        sort_column = getattr(PromptTemplateDB, search_request.sort_by)
        if search_request.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Apply pagination
        query = query.offset(search_request.offset).limit(search_request.limit)
        
        templates = query.all()
        
        return [PromptTemplateResponse.from_orm(template) for template in templates]
    
    async def render_template(
        self,
        db: Session,
        template_id: str,
        variables: Dict[str, Any]
    ) -> str:
        """Render a template with provided variables."""
        
        db_template = db.query(PromptTemplateDB).filter(
            PromptTemplateDB.id == template_id
        ).first()
        
        if not db_template:
            raise TemplateNotFoundError(template_id)
        
        try:
            template = Template(db_template.template)
            rendered = template.render(**variables)
            
            # Update usage count
            db_template.usage_count += 1
            db.commit()
            
            self.logger.info(
                "Template rendered",
                template_id=template_id,
                variables_count=len(variables)
            )
            
            return rendered
            
        except Exception as e:
            raise ValidationError(f"Template rendering failed: {str(e)}", "variables")
    
    async def rate_template(
        self,
        db: Session,
        template_id: str,
        rating: float
    ) -> PromptTemplateResponse:
        """Rate a template."""
        
        db_template = db.query(PromptTemplateDB).filter(
            PromptTemplateDB.id == template_id
        ).first()
        
        if not db_template:
            raise TemplateNotFoundError(template_id)
        
        # Update rating (simple average)
        total_rating = db_template.rating * db_template.rating_count + rating
        db_template.rating_count += 1
        db_template.rating = total_rating / db_template.rating_count
        
        db.commit()
        db.refresh(db_template)
        
        self.logger.info("Template rated", template_id=template_id, rating=rating)
        
        return PromptTemplateResponse.from_orm(db_template)


# Global template service instance
template_service = TemplateService()
