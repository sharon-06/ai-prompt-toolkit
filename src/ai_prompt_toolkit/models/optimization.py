"""
Models for prompt optimization.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime, JSON, Float, Integer, Boolean
from pydantic import BaseModel, Field

from ai_prompt_toolkit.core.database import Base


class OptimizationStatus(str, Enum):
    """Optimization job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OptimizationMetric(str, Enum):
    """Optimization metrics."""
    COST = "cost"
    PERFORMANCE = "performance"
    LATENCY = "latency"
    QUALITY = "quality"
    SAFETY = "safety"


class OptimizationJobDB(Base):
    """Database model for optimization jobs."""
    
    __tablename__ = "optimization_jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    original_prompt = Column(Text, nullable=False)
    optimized_prompt = Column(Text)
    status = Column(String(20), default=OptimizationStatus.PENDING.value)
    target_metrics = Column(JSON, default=list)  # List of metrics to optimize
    optimization_config = Column(JSON, default=dict)
    results = Column(JSON, default=dict)
    iterations = Column(Integer, default=0)
    max_iterations = Column(Integer, default=5)
    cost_original = Column(Float)
    cost_optimized = Column(Float)
    performance_original = Column(Float)
    performance_optimized = Column(Float)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)


class OptimizationRequest(BaseModel):
    """Schema for optimization request."""
    
    prompt: str = Field(..., min_length=1, max_length=10000)
    target_metrics: List[OptimizationMetric] = Field(default=[OptimizationMetric.COST, OptimizationMetric.PERFORMANCE])
    max_iterations: int = Field(default=5, ge=1, le=20)
    target_cost_reduction: float = Field(default=0.2, ge=0.0, le=0.9)
    performance_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    use_genetic_algorithm: bool = True
    population_size: int = Field(default=10, ge=5, le=50)
    test_cases: Optional[List[Dict[str, Any]]] = None
    context: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None


class OptimizationResponse(BaseModel):
    """Schema for optimization response."""
    
    job_id: str
    status: OptimizationStatus
    original_prompt: str
    optimized_prompt: Optional[str]
    iterations: int
    max_iterations: int
    cost_reduction: Optional[float]
    performance_change: Optional[float]
    results: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class PromptVariant(BaseModel):
    """Schema for prompt variants during optimization."""
    
    prompt: str
    score: float
    metrics: Dict[str, float]
    generation: int
    parent_id: Optional[str] = None


class OptimizationIteration(BaseModel):
    """Schema for optimization iteration results."""
    
    iteration: int
    variants: List[PromptVariant]
    best_variant: PromptVariant
    improvement: float
    timestamp: datetime


class PromptEvaluation(BaseModel):
    """Schema for prompt evaluation results."""
    
    prompt: str
    cost_score: float
    performance_score: float
    quality_score: float
    safety_score: float
    latency_score: float
    overall_score: float
    test_results: List[Dict[str, Any]]
    token_count: int
    estimated_cost: float


class OptimizationTechnique(str, Enum):
    """Available optimization techniques."""
    GENETIC_ALGORITHM = "genetic_algorithm"
    HILL_CLIMBING = "hill_climbing"
    SIMULATED_ANNEALING = "simulated_annealing"
    RANDOM_SEARCH = "random_search"
    GRADIENT_FREE = "gradient_free"


class OptimizationConfig(BaseModel):
    """Configuration for optimization algorithms."""
    
    technique: OptimizationTechnique = OptimizationTechnique.GENETIC_ALGORITHM
    population_size: int = Field(default=10, ge=5, le=50)
    mutation_rate: float = Field(default=0.1, ge=0.01, le=0.5)
    crossover_rate: float = Field(default=0.8, ge=0.1, le=1.0)
    elite_size: int = Field(default=2, ge=1, le=10)
    max_generations: int = Field(default=10, ge=1, le=50)
    convergence_threshold: float = Field(default=0.01, ge=0.001, le=0.1)
    diversity_threshold: float = Field(default=0.1, ge=0.01, le=0.5)
