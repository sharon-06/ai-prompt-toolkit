"""
Prompt optimization API endpoints.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from ai_prompt_toolkit.core.database import get_db
from ai_prompt_toolkit.models.optimization import (
    OptimizationRequest,
    OptimizationResponse,
    PromptEvaluation
)
from ai_prompt_toolkit.services.optimization_service import prompt_optimizer
from ai_prompt_toolkit.security.injection_detector import injection_detector
from ai_prompt_toolkit.security.guardrails import guardrail_engine
from ai_prompt_toolkit.utils.prompt_analyzer import PromptAnalyzer
from ai_prompt_toolkit.utils.cost_calculator import CostCalculator
from ai_prompt_toolkit.core.config import settings, LLMProvider

router = APIRouter()
analyzer = PromptAnalyzer()
cost_calculator = CostCalculator()


@router.post("/optimize", response_model=Dict[str, str])
async def optimize_prompt(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start prompt optimization job."""
    # Validate prompt for injection attacks
    injection_detector.validate_prompt(request.prompt)
    
    job_id = await prompt_optimizer.optimize_prompt(db, request)
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": "Optimization job started. Use the job_id to check status."
    }


@router.get("/jobs/{job_id}", response_model=OptimizationResponse)
async def get_optimization_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get optimization job status and results."""
    return await prompt_optimizer.get_optimization_status(db, job_id)


@router.post("/analyze")
async def analyze_prompt(prompt: Dict[str, str]):
    """Analyze a prompt for quality metrics."""
    prompt_text = prompt.get("prompt", "")
    
    if not prompt_text:
        raise HTTPException(status_code=400, detail="Prompt text is required")
    
    # Validate prompt for injection attacks
    injection_detector.validate_prompt(prompt_text)
    
    # Analyze prompt
    analysis = await analyzer.analyze_prompt(prompt_text)
    
    return {
        "prompt": prompt_text,
        "analysis": analysis,
        "recommendations": _get_improvement_recommendations(analysis)
    }


@router.post("/evaluate")
async def evaluate_prompt(
    request: Dict[str, Any]
):
    """Evaluate a prompt with test cases."""
    prompt_text = request.get("prompt", "")
    test_cases = request.get("test_cases", [])
    
    if not prompt_text:
        raise HTTPException(status_code=400, detail="Prompt text is required")
    
    # Validate prompt for injection attacks
    injection_detector.validate_prompt(prompt_text)
    
    # Evaluate prompt
    evaluation = await prompt_optimizer._evaluate_prompt(prompt_text, test_cases)
    
    return evaluation.dict()


@router.post("/cost-estimate")
async def estimate_cost(
    request: Dict[str, Any]
):
    """Estimate cost for a prompt across different providers."""
    prompt_text = request.get("prompt", "")
    monthly_requests = request.get("monthly_requests", 1000)
    
    if not prompt_text:
        raise HTTPException(status_code=400, detail="Prompt text is required")
    
    # Analyze prompt to get token count
    analysis = await analyzer.analyze_prompt(prompt_text)
    token_count = analysis["token_count"]
    
    # Calculate costs for all providers
    cost_comparison = cost_calculator.compare_provider_costs(token_count)
    
    # Calculate monthly estimates
    monthly_estimates = {}
    for provider_name, cost_per_request in cost_comparison.items():
        provider = LLMProvider(provider_name)
        monthly_cost = cost_per_request * monthly_requests
        monthly_estimates[provider_name] = {
            "cost_per_request": cost_per_request,
            "monthly_cost": monthly_cost,
            "yearly_cost": monthly_cost * 12
        }
    
    return {
        "prompt": prompt_text,
        "token_count": token_count,
        "monthly_requests": monthly_requests,
        "cost_estimates": monthly_estimates,
        "cheapest_provider": min(cost_comparison.items(), key=lambda x: x[1])[0],
        "most_expensive_provider": max(cost_comparison.items(), key=lambda x: x[1])[0]
    }


@router.post("/compare-optimization")
async def compare_optimization_results(
    request: Dict[str, Any]
):
    """Compare original vs optimized prompt costs and performance."""
    original_prompt = request.get("original_prompt", "")
    optimized_prompt = request.get("optimized_prompt", "")
    monthly_requests = request.get("monthly_requests", 1000)
    provider = request.get("provider", settings.default_llm_provider.value)
    
    if not original_prompt or not optimized_prompt:
        raise HTTPException(
            status_code=400,
            detail="Both original_prompt and optimized_prompt are required"
        )
    
    # Analyze both prompts
    original_analysis = await analyzer.analyze_prompt(original_prompt)
    optimized_analysis = await analyzer.analyze_prompt(optimized_prompt)
    
    # Calculate cost savings
    provider_enum = LLMProvider(provider)
    savings = cost_calculator.calculate_optimization_savings(
        original_analysis["token_count"],
        optimized_analysis["token_count"],
        provider_enum,
        monthly_requests
    )
    
    return {
        "original_prompt": {
            "text": original_prompt,
            "analysis": original_analysis
        },
        "optimized_prompt": {
            "text": optimized_prompt,
            "analysis": optimized_analysis
        },
        "savings": savings,
        "improvement_summary": {
            "token_reduction": savings["token_reduction"],
            "cost_savings_monthly": savings["monthly_savings"],
            "cost_savings_yearly": savings["yearly_savings"],
            "percentage_improvement": savings["percentage_savings"]
        }
    }


def _get_improvement_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """Generate improvement recommendations based on analysis."""
    recommendations = []
    
    if analysis["clarity_score"] < 0.7:
        recommendations.append("Consider making instructions more clear and specific")
    
    if analysis["quality_score"] < 0.7:
        recommendations.append("Add more context and examples to improve quality")
    
    if analysis["token_count"] > 1000:
        recommendations.append("Consider reducing prompt length to save costs")
    
    if not analysis["has_examples"]:
        recommendations.append("Add examples to improve AI understanding")
    
    if not analysis["has_constraints"]:
        recommendations.append("Add constraints or requirements for better control")
    
    if analysis["instruction_count"] == 0:
        recommendations.append("Add clear action verbs (write, analyze, create, etc.)")
    
    if analysis["complexity_level"] == "complex":
        recommendations.append("Consider breaking down into simpler instructions")
    
    for issue in analysis["potential_issues"]:
        recommendations.append(f"Fix issue: {issue}")
    
    if not recommendations:
        recommendations.append("Prompt looks good! Consider testing with different inputs.")
    
    return recommendations
