"""
Enhanced guardrails system integrating guardrails-ai with existing custom rules.
Provides comprehensive validation for prompt optimization workflows.
"""

import re
import json
from typing import Dict, List, Any, Tuple, Optional, Union
from enum import Enum
from dataclasses import dataclass
import structlog
import asyncio
from functools import wraps

from ai_prompt_toolkit.core.exceptions import GuardrailViolation
from ai_prompt_toolkit.security.injection_detector import injection_detector
from ai_prompt_toolkit.security.guardrails import GuardrailEngine, GuardrailType, ViolationSeverity

# Import guardrails-ai with fallback
try:
    import guardrails as gd
    from guardrails import Guard
    from guardrails.hub import CompetitorCheck, ToxicLanguage, ProfanityFree, NoInvalidLinks, ValidChoices
    from guardrails.validators import ValidatorError
    GUARDRAILS_AI_AVAILABLE = True
except ImportError:
    GUARDRAILS_AI_AVAILABLE = False
    print("Warning: guardrails-ai not available. Install with: pip install guardrails-ai")


@dataclass
class EnhancedGuardrailResult:
    """Enhanced result combining custom and guardrails-ai validation."""
    is_safe: bool
    passed: bool
    violations: List[Dict[str, Any]]
    guardrails_ai_result: Optional[Dict[str, Any]] = None
    custom_result: Optional[Dict[str, Any]] = None
    recommendations: List[str] = None
    summary: Dict[str, Any] = None


class EnhancedGuardrailEngine:
    """Enhanced guardrails engine combining custom rules with guardrails-ai."""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.custom_engine = GuardrailEngine()
        self.guardrails_ai_enabled = GUARDRAILS_AI_AVAILABLE
        
        # Initialize guardrails-ai guards if available
        if self.guardrails_ai_enabled:
            self._initialize_guardrails_ai()
        else:
            self.logger.warning("Guardrails-AI not available, using custom rules only")
    
    def _initialize_guardrails_ai(self):
        """Initialize guardrails-ai guards for different use cases."""
        try:
            # Guard for prompt validation
            self.prompt_guard = Guard().use(
                ToxicLanguage(threshold=0.8, validation_method="sentence"),
                ProfanityFree(),
                NoInvalidLinks(),
                on_fail="exception"
            )
            
            # Guard for response validation
            self.response_guard = Guard().use(
                ToxicLanguage(threshold=0.7, validation_method="sentence"),
                ProfanityFree(),
                on_fail="filter"
            )
            
            # Guard for code generation
            self.code_guard = Guard().use(
                ValidChoices(choices=["python", "javascript", "sql", "bash"], on_fail="reask"),
                on_fail="exception"
            )
            
            self.logger.info("Guardrails-AI guards initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize guardrails-ai", error=str(e))
            self.guardrails_ai_enabled = False
    
    async def validate_prompt(self, prompt: str, context: Dict[str, Any] = None) -> EnhancedGuardrailResult:
        """Enhanced prompt validation using both custom and guardrails-ai."""
        
        # Run custom validation
        custom_result = self.custom_engine.validate_prompt(prompt, strict_mode=False)
        
        # Run guardrails-ai validation if available
        guardrails_ai_result = None
        if self.guardrails_ai_enabled:
            guardrails_ai_result = await self._validate_with_guardrails_ai(prompt, "prompt")
        
        # Combine results
        combined_result = self._combine_results(custom_result, guardrails_ai_result)
        
        return EnhancedGuardrailResult(
            is_safe=combined_result["is_safe"],
            passed=combined_result["passed"],
            violations=combined_result["violations"],
            guardrails_ai_result=guardrails_ai_result,
            custom_result=custom_result,
            recommendations=combined_result["recommendations"],
            summary=combined_result["summary"]
        )
    
    async def validate_response(self, response: str, original_prompt: str = "", context: Dict[str, Any] = None) -> EnhancedGuardrailResult:
        """Enhanced response validation using both custom and guardrails-ai."""
        
        # Run custom validation
        custom_result = self.custom_engine.validate_response(response, original_prompt)
        
        # Run guardrails-ai validation if available
        guardrails_ai_result = None
        if self.guardrails_ai_enabled:
            guardrails_ai_result = await self._validate_with_guardrails_ai(response, "response")
        
        # Combine results
        combined_result = self._combine_results(custom_result, guardrails_ai_result)
        
        return EnhancedGuardrailResult(
            is_safe=combined_result["is_safe"],
            passed=combined_result["passed"],
            violations=combined_result["violations"],
            guardrails_ai_result=guardrails_ai_result,
            custom_result=custom_result,
            recommendations=combined_result["recommendations"],
            summary=combined_result["summary"]
        )
    
    async def validate_code_generation(self, prompt: str, generated_code: str, language: str = "python") -> EnhancedGuardrailResult:
        """Specialized validation for code generation prompts and outputs."""
        
        # Validate the prompt first
        prompt_result = await self.validate_prompt(prompt)
        
        # Additional code-specific validation
        code_violations = []
        
        # Check for dangerous code patterns
        dangerous_patterns = [
            r'import\s+os.*system',
            r'subprocess\.(call|run|Popen)',
            r'eval\s*\(',
            r'exec\s*\(',
            r'__import__',
            r'open\s*\([^)]*["\']w["\']',  # File writing
            r'rm\s+-rf',
            r'del\s+.*\*'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, generated_code, re.IGNORECASE):
                code_violations.append({
                    "rule_name": "dangerous_code_pattern",
                    "rule_type": "code_safety",
                    "severity": "error",
                    "description": f"Potentially dangerous code pattern detected: {pattern}",
                    "matched_text": pattern,
                    "recommendation": "Review and sanitize the generated code"
                })
        
        # Combine with prompt validation results
        all_violations = prompt_result.violations + code_violations
        is_safe = prompt_result.is_safe and len(code_violations) == 0
        
        return EnhancedGuardrailResult(
            is_safe=is_safe,
            passed=is_safe,
            violations=all_violations,
            recommendations=prompt_result.recommendations + ["Review generated code for security issues"],
            summary={
                "total_violations": len(all_violations),
                "prompt_violations": len(prompt_result.violations),
                "code_violations": len(code_violations)
            }
        )
    
    async def _validate_with_guardrails_ai(self, text: str, validation_type: str) -> Dict[str, Any]:
        """Validate text using guardrails-ai."""
        try:
            if validation_type == "prompt":
                guard = self.prompt_guard
            elif validation_type == "response":
                guard = self.response_guard
            elif validation_type == "code":
                guard = self.code_guard
            else:
                guard = self.prompt_guard
            
            # Run validation
            result = guard.validate(text)
            
            return {
                "passed": result.validation_passed,
                "validated_output": result.validated_output,
                "error": None,
                "raw_result": result
            }
            
        except Exception as e:
            self.logger.error("Guardrails-AI validation failed", error=str(e))
            return {
                "passed": False,
                "validated_output": None,
                "error": str(e),
                "raw_result": None
            }
    
    def _combine_results(self, custom_result: Dict[str, Any], guardrails_ai_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine results from custom and guardrails-ai validation."""
        
        # Start with custom results
        combined_violations = custom_result.get("violations", [])
        combined_recommendations = custom_result.get("recommendations", [])
        
        # Add guardrails-ai violations if available
        if guardrails_ai_result and not guardrails_ai_result.get("passed", True):
            guardrails_ai_violations = [{
                "rule_name": "guardrails_ai_validation",
                "rule_type": "external_validation",
                "severity": "error",
                "description": "Guardrails-AI validation failed",
                "matched_text": guardrails_ai_result.get("error", "Unknown error"),
                "recommendation": "Review content for policy violations"
            }]
            combined_violations.extend(guardrails_ai_violations)
            combined_recommendations.append("Content failed external validation checks")
        
        # Determine overall safety
        custom_safe = custom_result.get("is_safe", True)
        guardrails_ai_safe = guardrails_ai_result.get("passed", True) if guardrails_ai_result else True
        
        overall_safe = custom_safe and guardrails_ai_safe
        
        return {
            "is_safe": overall_safe,
            "passed": overall_safe,
            "violations": combined_violations,
            "recommendations": combined_recommendations,
            "summary": {
                "total_violations": len(combined_violations),
                "custom_violations": len(custom_result.get("violations", [])),
                "guardrails_ai_violations": 1 if guardrails_ai_result and not guardrails_ai_result.get("passed", True) else 0,
                "overall_safe": overall_safe
            }
        }
    
    def get_guardrail_stats(self) -> Dict[str, Any]:
        """Get comprehensive guardrail statistics."""
        custom_stats = self.custom_engine.get_guardrail_stats()
        
        return {
            "custom_engine": custom_stats,
            "guardrails_ai_enabled": self.guardrails_ai_enabled,
            "total_engines": 2 if self.guardrails_ai_enabled else 1,
            "capabilities": {
                "prompt_validation": True,
                "response_validation": True,
                "code_validation": self.guardrails_ai_enabled,
                "injection_detection": True,
                "toxicity_detection": self.guardrails_ai_enabled,
                "profanity_filtering": self.guardrails_ai_enabled
            }
        }
    
    async def validate_optimization_request(self, original_prompt: str, optimized_prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Specialized validation for prompt optimization workflows."""
        
        # Validate both prompts
        original_result = await self.validate_prompt(original_prompt, context)
        optimized_result = await self.validate_prompt(optimized_prompt, context)
        
        # Check if optimization maintained safety
        safety_maintained = optimized_result.is_safe >= original_result.is_safe
        
        # Check if optimization improved quality
        original_violations = len(original_result.violations)
        optimized_violations = len(optimized_result.violations)
        quality_improved = optimized_violations <= original_violations
        
        return {
            "original_validation": original_result,
            "optimized_validation": optimized_result,
            "safety_maintained": safety_maintained,
            "quality_improved": quality_improved,
            "optimization_safe": safety_maintained and optimized_result.is_safe,
            "recommendations": [
                "Optimization maintained safety standards" if safety_maintained else "Optimization may have introduced safety issues",
                "Optimization improved quality" if quality_improved else "Optimization may have introduced new issues"
            ]
        }


# Global enhanced guardrail engine instance
enhanced_guardrail_engine = EnhancedGuardrailEngine()


# Decorator for automatic guardrail validation
def with_guardrails(validation_type: str = "prompt"):
    """Decorator to automatically validate inputs/outputs with guardrails."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract text to validate (assumes first string argument)
            text_to_validate = None
            for arg in args:
                if isinstance(arg, str) and len(arg) > 10:  # Reasonable text length
                    text_to_validate = arg
                    break
            
            if text_to_validate:
                if validation_type == "prompt":
                    validation_result = await enhanced_guardrail_engine.validate_prompt(text_to_validate)
                elif validation_type == "response":
                    validation_result = await enhanced_guardrail_engine.validate_response(text_to_validate)
                else:
                    validation_result = await enhanced_guardrail_engine.validate_prompt(text_to_validate)
                
                if not validation_result.is_safe:
                    raise GuardrailViolation(
                        f"Guardrail validation failed: {validation_result.violations}",
                        violations=validation_result.violations
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
