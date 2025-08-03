"""
Cost calculation utilities for different LLM providers.
"""

from typing import Dict, Any
import structlog

from ai_prompt_toolkit.core.config import LLMProvider


class CostCalculator:
    """Calculator for LLM usage costs."""
    
    # Cost per 1K tokens (approximate, as of 2024)
    COST_PER_1K_TOKENS = {
        LLMProvider.OLLAMA: 0.0,  # Local model, no API cost
        LLMProvider.OPENAI: {
            "gpt-3.5-turbo": 0.002,
            "gpt-4": 0.03,
            "gpt-4-turbo": 0.01,
        },
        LLMProvider.ANTHROPIC: {
            "claude-3-sonnet": 0.015,
            "claude-3-haiku": 0.0025,
            "claude-3-opus": 0.075,
        },
        LLMProvider.BEDROCK: {
            "anthropic.claude-v2": 0.008,
            "anthropic.claude-instant-v1": 0.0016,
        }
    }
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
    
    def calculate_cost(
        self,
        token_count: int,
        provider: LLMProvider,
        model: str = None
    ) -> float:
        """Calculate cost for given token count and provider."""
        
        if provider == LLMProvider.OLLAMA:
            return 0.0  # Local model, no cost
        
        cost_data = self.COST_PER_1K_TOKENS.get(provider)
        if not cost_data:
            self.logger.warning("Unknown provider for cost calculation", provider=provider.value)
            return 0.0
        
        if isinstance(cost_data, dict):
            if not model:
                # Use first model as default
                model_cost = list(cost_data.values())[0]
            else:
                model_cost = cost_data.get(model, list(cost_data.values())[0])
        else:
            model_cost = cost_data
        
        # Calculate cost for the token count
        cost = (token_count / 1000) * model_cost
        
        return round(cost, 6)
    
    def estimate_monthly_cost(
        self,
        daily_requests: int,
        avg_tokens_per_request: int,
        provider: LLMProvider,
        model: str = None
    ) -> Dict[str, float]:
        """Estimate monthly costs based on usage patterns."""
        
        daily_cost = self.calculate_cost(
            daily_requests * avg_tokens_per_request,
            provider,
            model
        )
        
        return {
            "daily_cost": daily_cost,
            "weekly_cost": daily_cost * 7,
            "monthly_cost": daily_cost * 30,
            "yearly_cost": daily_cost * 365
        }
    
    def compare_provider_costs(
        self,
        token_count: int,
        providers: list[LLMProvider] = None
    ) -> Dict[str, float]:
        """Compare costs across different providers."""
        
        if providers is None:
            providers = list(LLMProvider)
        
        costs = {}
        for provider in providers:
            cost = self.calculate_cost(token_count, provider)
            costs[provider.value] = cost
        
        return costs
    
    def calculate_optimization_savings(
        self,
        original_tokens: int,
        optimized_tokens: int,
        provider: LLMProvider,
        monthly_requests: int = 1000,
        model: str = None
    ) -> Dict[str, Any]:
        """Calculate potential savings from prompt optimization."""
        
        original_cost_per_request = self.calculate_cost(original_tokens, provider, model)
        optimized_cost_per_request = self.calculate_cost(optimized_tokens, provider, model)
        
        savings_per_request = original_cost_per_request - optimized_cost_per_request
        monthly_savings = savings_per_request * monthly_requests
        yearly_savings = monthly_savings * 12
        
        percentage_savings = (savings_per_request / original_cost_per_request * 100) if original_cost_per_request > 0 else 0
        
        return {
            "original_cost_per_request": original_cost_per_request,
            "optimized_cost_per_request": optimized_cost_per_request,
            "savings_per_request": savings_per_request,
            "monthly_savings": monthly_savings,
            "yearly_savings": yearly_savings,
            "percentage_savings": round(percentage_savings, 2),
            "token_reduction": original_tokens - optimized_tokens,
            "token_reduction_percentage": round((original_tokens - optimized_tokens) / original_tokens * 100, 2) if original_tokens > 0 else 0
        }
    
    def get_cost_breakdown(
        self,
        token_count: int,
        provider: LLMProvider,
        model: str = None
    ) -> Dict[str, Any]:
        """Get detailed cost breakdown."""
        
        cost = self.calculate_cost(token_count, provider, model)
        cost_per_token = cost / token_count if token_count > 0 else 0
        
        return {
            "provider": provider.value,
            "model": model,
            "token_count": token_count,
            "total_cost": cost,
            "cost_per_token": cost_per_token,
            "cost_per_1k_tokens": cost_per_token * 1000,
            "estimated_words": token_count * 0.75,  # Rough approximation
            "cost_per_word": cost / (token_count * 0.75) if token_count > 0 else 0
        }
