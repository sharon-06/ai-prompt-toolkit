"""
Prompt template models and database schemas.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime, JSON, Float, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field, validator

from ai_prompt_toolkit.core.database import Base


class TemplateCategory(str, Enum):
    """Template categories."""
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    QUESTION_ANSWERING = "question_answering"
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    CREATIVE_WRITING = "creative_writing"
    CONVERSATION = "conversation"
    CUSTOM = "custom"


class PromptTemplateDB(Base):
    """Database model for prompt templates."""
    
    __tablename__ = "prompt_templates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(50), nullable=False, index=True)
    template = Column(Text, nullable=False)
    variables = Column(JSON, default=list)  # List of variable names
    tags = Column(JSON, default=list)  # List of tags
    version = Column(String(20), default="1.0.0")
    author = Column(String(255))
    is_public = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PromptTemplateCreate(BaseModel):
    """Schema for creating a prompt template."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: TemplateCategory
    template: str = Field(..., min_length=1)
    variables: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    version: str = Field(default="1.0.0", regex=r"^\d+\.\d+\.\d+$")
    author: Optional[str] = None
    is_public: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator("variables")
    def validate_variables(cls, v, values):
        """Validate that all variables in template are listed."""
        template = values.get("template", "")
        # Simple validation - in production, use proper template parsing
        import re
        template_vars = set(re.findall(r'\{(\w+)\}', template))
        declared_vars = set(v)
        
        missing_vars = template_vars - declared_vars
        if missing_vars:
            raise ValueError(f"Template contains undeclared variables: {missing_vars}")
        
        return v


class PromptTemplateUpdate(BaseModel):
    """Schema for updating a prompt template."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[TemplateCategory] = None
    template: Optional[str] = Field(None, min_length=1)
    variables: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    version: Optional[str] = Field(None, regex=r"^\d+\.\d+\.\d+$")
    author: Optional[str] = None
    is_public: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class PromptTemplateResponse(BaseModel):
    """Schema for prompt template response."""
    
    id: str
    name: str
    description: Optional[str]
    category: TemplateCategory
    template: str
    variables: List[str]
    tags: List[str]
    version: str
    author: Optional[str]
    is_public: bool
    usage_count: int
    rating: float
    rating_count: int
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PromptTemplateRating(BaseModel):
    """Schema for rating a prompt template."""
    
    rating: float = Field(..., ge=1.0, le=5.0)
    comment: Optional[str] = None


class TemplateSearchRequest(BaseModel):
    """Schema for searching templates."""
    
    query: Optional[str] = None
    category: Optional[TemplateCategory] = None
    tags: Optional[List[str]] = None
    author: Optional[str] = None
    is_public: Optional[bool] = True
    min_rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: str = Field(default="created_at", regex="^(created_at|updated_at|rating|usage_count|name)$")
    sort_order: str = Field(default="desc", regex="^(asc|desc)$")


class TemplateRenderRequest(BaseModel):
    """Schema for rendering a template with variables."""
    
    template_id: str
    variables: Dict[str, Any] = Field(default_factory=dict)


class TemplateRenderResponse(BaseModel):
    """Schema for template render response."""
    
    rendered_prompt: str
    template_id: str
    variables_used: Dict[str, Any]
