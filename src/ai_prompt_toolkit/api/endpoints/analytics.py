"""
Analytics and reporting API endpoints.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ai_prompt_toolkit.core.database import get_db
from ai_prompt_toolkit.models.prompt_template import PromptTemplateDB
from ai_prompt_toolkit.models.optimization import OptimizationJobDB
from ai_prompt_toolkit.utils.cost_calculator import CostCalculator

router = APIRouter()
cost_calculator = CostCalculator()


@router.get("/dashboard")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    
    # Template statistics
    total_templates = db.query(PromptTemplateDB).count()
    public_templates = db.query(PromptTemplateDB).filter(PromptTemplateDB.is_public == True).count()
    
    # Most popular templates
    popular_templates = db.query(PromptTemplateDB).order_by(
        desc(PromptTemplateDB.usage_count)
    ).limit(5).all()
    
    # Template categories distribution
    category_stats = db.query(
        PromptTemplateDB.category,
        func.count(PromptTemplateDB.id).label('count')
    ).group_by(PromptTemplateDB.category).all()
    
    # Optimization statistics
    total_optimizations = db.query(OptimizationJobDB).count()
    completed_optimizations = db.query(OptimizationJobDB).filter(
        OptimizationJobDB.status == 'completed'
    ).count()
    
    # Recent optimization jobs
    recent_optimizations = db.query(OptimizationJobDB).order_by(
        desc(OptimizationJobDB.created_at)
    ).limit(5).all()
    
    # Calculate average cost savings
    completed_jobs = db.query(OptimizationJobDB).filter(
        OptimizationJobDB.status == 'completed',
        OptimizationJobDB.cost_original.isnot(None),
        OptimizationJobDB.cost_optimized.isnot(None)
    ).all()
    
    total_savings = 0
    savings_count = 0
    for job in completed_jobs:
        if job.cost_original and job.cost_optimized:
            savings = job.cost_original - job.cost_optimized
            total_savings += savings
            savings_count += 1
    
    average_savings = total_savings / savings_count if savings_count > 0 else 0
    
    return {
        "templates": {
            "total": total_templates,
            "public": public_templates,
            "private": total_templates - public_templates,
            "popular": [
                {
                    "id": t.id,
                    "name": t.name,
                    "usage_count": t.usage_count,
                    "rating": t.rating
                }
                for t in popular_templates
            ],
            "categories": [
                {"category": cat, "count": count}
                for cat, count in category_stats
            ]
        },
        "optimizations": {
            "total": total_optimizations,
            "completed": completed_optimizations,
            "success_rate": (completed_optimizations / total_optimizations * 100) if total_optimizations > 0 else 0,
            "average_cost_savings": average_savings,
            "recent": [
                {
                    "id": opt.id,
                    "status": opt.status,
                    "created_at": opt.created_at,
                    "cost_reduction": (
                        (opt.cost_original - opt.cost_optimized) / opt.cost_original * 100
                        if opt.cost_original and opt.cost_optimized and opt.cost_original > 0
                        else None
                    )
                }
                for opt in recent_optimizations
            ]
        }
    }


@router.get("/templates/stats")
async def get_template_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get template usage statistics."""
    
    # Date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Templates created in period
    templates_created = db.query(PromptTemplateDB).filter(
        PromptTemplateDB.created_at >= start_date
    ).count()
    
    # Most used templates
    most_used = db.query(PromptTemplateDB).order_by(
        desc(PromptTemplateDB.usage_count)
    ).limit(10).all()
    
    # Top rated templates
    top_rated = db.query(PromptTemplateDB).filter(
        PromptTemplateDB.rating_count > 0
    ).order_by(desc(PromptTemplateDB.rating)).limit(10).all()
    
    # Category distribution
    category_distribution = db.query(
        PromptTemplateDB.category,
        func.count(PromptTemplateDB.id).label('count'),
        func.avg(PromptTemplateDB.rating).label('avg_rating'),
        func.sum(PromptTemplateDB.usage_count).label('total_usage')
    ).group_by(PromptTemplateDB.category).all()
    
    return {
        "period": {
            "days": days,
            "start_date": start_date,
            "end_date": end_date
        },
        "templates_created": templates_created,
        "most_used": [
            {
                "id": t.id,
                "name": t.name,
                "category": t.category,
                "usage_count": t.usage_count,
                "rating": t.rating
            }
            for t in most_used
        ],
        "top_rated": [
            {
                "id": t.id,
                "name": t.name,
                "category": t.category,
                "rating": t.rating,
                "rating_count": t.rating_count
            }
            for t in top_rated
        ],
        "category_stats": [
            {
                "category": cat,
                "template_count": count,
                "average_rating": float(avg_rating) if avg_rating else 0,
                "total_usage": int(total_usage) if total_usage else 0
            }
            for cat, count, avg_rating, total_usage in category_distribution
        ]
    }


@router.get("/optimization/stats")
async def get_optimization_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get optimization statistics."""
    
    # Date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Jobs in period
    jobs_in_period = db.query(OptimizationJobDB).filter(
        OptimizationJobDB.created_at >= start_date
    ).all()
    
    # Status distribution
    status_counts = {}
    for job in jobs_in_period:
        status_counts[job.status] = status_counts.get(job.status, 0) + 1
    
    # Calculate savings
    completed_jobs = [j for j in jobs_in_period if j.status == 'completed']
    total_original_cost = sum(j.cost_original for j in completed_jobs if j.cost_original)
    total_optimized_cost = sum(j.cost_optimized for j in completed_jobs if j.cost_optimized)
    total_savings = total_original_cost - total_optimized_cost
    
    # Performance improvements
    performance_improvements = []
    for job in completed_jobs:
        if job.performance_original and job.performance_optimized:
            improvement = job.performance_optimized - job.performance_original
            performance_improvements.append(improvement)
    
    avg_performance_improvement = (
        sum(performance_improvements) / len(performance_improvements)
        if performance_improvements else 0
    )
    
    return {
        "period": {
            "days": days,
            "start_date": start_date,
            "end_date": end_date
        },
        "total_jobs": len(jobs_in_period),
        "status_distribution": status_counts,
        "cost_savings": {
            "total_original_cost": total_original_cost,
            "total_optimized_cost": total_optimized_cost,
            "total_savings": total_savings,
            "average_savings_per_job": total_savings / len(completed_jobs) if completed_jobs else 0,
            "savings_percentage": (total_savings / total_original_cost * 100) if total_original_cost > 0 else 0
        },
        "performance": {
            "average_improvement": avg_performance_improvement,
            "jobs_with_improvement": len([i for i in performance_improvements if i > 0]),
            "jobs_with_degradation": len([i for i in performance_improvements if i < 0])
        }
    }


@router.get("/cost-analysis")
async def get_cost_analysis(
    provider: str = Query(None),
    monthly_requests: int = Query(1000, ge=1)
):
    """Get cost analysis and projections."""
    
    # Sample token counts for analysis
    sample_prompts = [
        {"name": "Simple Query", "tokens": 50},
        {"name": "Medium Prompt", "tokens": 200},
        {"name": "Complex Prompt", "tokens": 500},
        {"name": "Long Form", "tokens": 1000}
    ]
    
    cost_analysis = []
    
    for prompt_type in sample_prompts:
        token_count = prompt_type["tokens"]
        
        if provider:
            try:
                from ai_prompt_toolkit.core.config import LLMProvider
                provider_enum = LLMProvider(provider)
                cost = cost_calculator.calculate_cost(token_count, provider_enum)
                monthly_cost = cost * monthly_requests
                
                cost_analysis.append({
                    "prompt_type": prompt_type["name"],
                    "token_count": token_count,
                    "provider": provider,
                    "cost_per_request": cost,
                    "monthly_cost": monthly_cost,
                    "yearly_cost": monthly_cost * 12
                })
            except ValueError:
                continue
        else:
            # Compare all providers
            provider_costs = cost_calculator.compare_provider_costs(token_count)
            
            cost_analysis.append({
                "prompt_type": prompt_type["name"],
                "token_count": token_count,
                "provider_costs": {
                    provider_name: {
                        "cost_per_request": cost,
                        "monthly_cost": cost * monthly_requests,
                        "yearly_cost": cost * monthly_requests * 12
                    }
                    for provider_name, cost in provider_costs.items()
                }
            })
    
    return {
        "monthly_requests": monthly_requests,
        "cost_analysis": cost_analysis,
        "recommendations": [
            "Use local models (Ollama) for development and testing",
            "Consider prompt optimization to reduce token usage",
            "Monitor usage patterns to choose the most cost-effective provider",
            "Implement caching for repeated queries",
            "Use batch processing when possible"
        ]
    }


@router.get("/usage-trends")
async def get_usage_trends(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db)
):
    """Get usage trends over time."""
    
    # This is a simplified version - in production, you'd want proper time-series data
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Daily template usage (simplified)
    daily_stats = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        next_date = date + timedelta(days=1)
        
        templates_created = db.query(PromptTemplateDB).filter(
            PromptTemplateDB.created_at >= date,
            PromptTemplateDB.created_at < next_date
        ).count()
        
        optimizations_started = db.query(OptimizationJobDB).filter(
            OptimizationJobDB.created_at >= date,
            OptimizationJobDB.created_at < next_date
        ).count()
        
        daily_stats.append({
            "date": date.strftime("%Y-%m-%d"),
            "templates_created": templates_created,
            "optimizations_started": optimizations_started
        })
    
    return {
        "period": {
            "days": days,
            "start_date": start_date,
            "end_date": end_date
        },
        "daily_stats": daily_stats,
        "summary": {
            "total_templates_created": sum(d["templates_created"] for d in daily_stats),
            "total_optimizations": sum(d["optimizations_started"] for d in daily_stats),
            "average_daily_templates": sum(d["templates_created"] for d in daily_stats) / days,
            "average_daily_optimizations": sum(d["optimizations_started"] for d in daily_stats) / days
        }
    }
