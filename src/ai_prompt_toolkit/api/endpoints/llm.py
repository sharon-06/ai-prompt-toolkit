"""
LLM interaction API endpoints.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ai_prompt_toolkit.core.database import get_db
from ai_prompt_toolkit.core.config import settings, LLMProvider
from ai_prompt_toolkit.services.llm_factory import llm_factory
from ai_prompt_toolkit.security.injection_detector import injection_detector
from ai_prompt_toolkit.utils.prompt_analyzer import PromptAnalyzer
from ai_prompt_toolkit.utils.cost_calculator import CostCalculator

router = APIRouter()
analyzer = PromptAnalyzer()
cost_calculator = CostCalculator()


@router.get("/providers")
async def list_providers():
    """List available LLM providers and their status."""
    available_providers = llm_factory.get_available_providers()
    enabled_providers = settings.get_enabled_providers()
    
    providers_info = []
    for provider in LLMProvider:
        config = settings.get_provider_config(provider)
        providers_info.append({
            "name": provider.value,
            "enabled": provider in enabled_providers,
            "available": provider in available_providers,
            "is_default": provider == settings.default_llm_provider,
            "config": {
                "model": config.get("model", "N/A"),
                "temperature": config.get("temperature", "N/A"),
                "max_tokens": config.get("max_tokens", "N/A")
            }
        })
    
    return {
        "providers": providers_info,
        "default_provider": settings.default_llm_provider.value,
        "total_available": len(available_providers)
    }


@router.post("/generate")
async def generate_text(request: Dict[str, Any]):
    """Generate text using specified LLM provider."""
    prompt = request.get("prompt", "")
    provider_name = request.get("provider", settings.default_llm_provider.value)
    temperature = request.get("temperature")
    max_tokens = request.get("max_tokens")
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    # Validate prompt for injection attacks
    injection_detector.validate_prompt(prompt)
    
    try:
        provider = LLMProvider(provider_name)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider_name}")
    
    if not llm_factory.is_provider_available(provider):
        raise HTTPException(status_code=503, detail=f"Provider {provider_name} is not available")
    
    try:
        llm = llm_factory.get_llm(provider)
        
        # Override parameters if provided
        if temperature is not None:
            llm.temperature = temperature
        if max_tokens is not None:
            llm.max_tokens = max_tokens
        
        # Generate response
        result = await llm.agenerate([prompt])
        generated_text = result.generations[0][0].text
        
        # Calculate cost
        analysis = await analyzer.analyze_prompt(prompt + generated_text)
        cost = cost_calculator.calculate_cost(
            analysis["token_count"],
            provider
        )
        
        return {
            "prompt": prompt,
            "generated_text": generated_text,
            "provider": provider_name,
            "metadata": {
                "token_count": analysis["token_count"],
                "estimated_cost": cost,
                "temperature": temperature or llm.temperature,
                "max_tokens": max_tokens or getattr(llm, 'max_tokens', None)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/batch-generate")
async def batch_generate(request: Dict[str, Any]):
    """Generate text for multiple prompts."""
    prompts = request.get("prompts", [])
    provider_name = request.get("provider", settings.default_llm_provider.value)
    
    if not prompts:
        raise HTTPException(status_code=400, detail="Prompts list is required")
    
    if len(prompts) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 prompts allowed per batch")
    
    # Validate all prompts
    for prompt in prompts:
        injection_detector.validate_prompt(prompt)
    
    try:
        provider = LLMProvider(provider_name)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider_name}")
    
    if not llm_factory.is_provider_available(provider):
        raise HTTPException(status_code=503, detail=f"Provider {provider_name} is not available")
    
    try:
        llm = llm_factory.get_llm(provider)
        
        # Generate responses
        results = []
        total_cost = 0
        
        for i, prompt in enumerate(prompts):
            result = await llm.agenerate([prompt])
            generated_text = result.generations[0][0].text
            
            # Calculate cost
            analysis = await analyzer.analyze_prompt(prompt + generated_text)
            cost = cost_calculator.calculate_cost(
                analysis["token_count"],
                provider
            )
            total_cost += cost
            
            results.append({
                "index": i,
                "prompt": prompt,
                "generated_text": generated_text,
                "token_count": analysis["token_count"],
                "cost": cost
            })
        
        return {
            "results": results,
            "provider": provider_name,
            "summary": {
                "total_prompts": len(prompts),
                "total_cost": total_cost,
                "average_cost": total_cost / len(prompts) if prompts else 0
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch generation failed: {str(e)}")


@router.post("/test-prompt")
async def test_prompt(request: Dict[str, Any]):
    """Test a prompt with multiple providers for comparison."""
    prompt = request.get("prompt", "")
    providers = request.get("providers", [])
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    # Validate prompt
    injection_detector.validate_prompt(prompt)
    
    if not providers:
        providers = [p.value for p in llm_factory.get_available_providers()]
    
    results = []
    for provider_name in providers:
        try:
            provider = LLMProvider(provider_name)
            if not llm_factory.is_provider_available(provider):
                continue
            
            llm = llm_factory.get_llm(provider)
            result = await llm.agenerate([prompt])
            generated_text = result.generations[0][0].text
            
            # Calculate metrics
            analysis = await analyzer.analyze_prompt(prompt + generated_text)
            cost = cost_calculator.calculate_cost(analysis["token_count"], provider)
            
            results.append({
                "provider": provider_name,
                "generated_text": generated_text,
                "token_count": analysis["token_count"],
                "cost": cost,
                "success": True
            })
        
        except Exception as e:
            results.append({
                "provider": provider_name,
                "error": str(e),
                "success": False
            })
    
    return {
        "prompt": prompt,
        "results": results,
        "comparison": {
            "cheapest": min([r for r in results if r["success"]], key=lambda x: x["cost"], default=None),
            "most_expensive": max([r for r in results if r["success"]], key=lambda x: x["cost"], default=None),
            "average_cost": sum(r["cost"] for r in results if r["success"]) / len([r for r in results if r["success"]]) if any(r["success"] for r in results) else 0
        }
    }


@router.get("/health")
async def check_llm_health():
    """Check health status of all LLM providers."""
    health_status = {}
    
    for provider in LLMProvider:
        try:
            if llm_factory.is_provider_available(provider):
                # Try a simple generation to test health
                llm = llm_factory.get_llm(provider)
                test_result = await llm.agenerate(["Hello"])
                health_status[provider.value] = {
                    "status": "healthy",
                    "available": True,
                    "test_successful": True
                }
            else:
                health_status[provider.value] = {
                    "status": "unavailable",
                    "available": False,
                    "test_successful": False
                }
        except Exception as e:
            health_status[provider.value] = {
                "status": "error",
                "available": False,
                "test_successful": False,
                "error": str(e)
            }
    
    overall_health = "healthy" if any(
        status["status"] == "healthy" for status in health_status.values()
    ) else "degraded"
    
    return {
        "overall_health": overall_health,
        "providers": health_status,
        "healthy_count": sum(1 for s in health_status.values() if s["status"] == "healthy"),
        "total_count": len(health_status)
    }
