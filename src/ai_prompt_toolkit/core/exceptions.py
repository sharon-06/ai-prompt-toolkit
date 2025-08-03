"""
Custom exceptions for AI Prompt Toolkit.
"""

from typing import Any, Dict, Optional


class AIPromptToolkitException(Exception):
    """Base exception for AI Prompt Toolkit."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(AIPromptToolkitException):
    """Configuration related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details=details
        )


class LLMProviderError(AIPromptToolkitException):
    """LLM provider related errors."""
    
    def __init__(self, message: str, provider: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="LLM_PROVIDER_ERROR",
            status_code=503,
            details={**(details or {}), "provider": provider}
        )


class PromptOptimizationError(AIPromptToolkitException):
    """Prompt optimization related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="PROMPT_OPTIMIZATION_ERROR",
            status_code=422,
            details=details
        )


class PromptInjectionDetected(AIPromptToolkitException):
    """Prompt injection attack detected."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="PROMPT_INJECTION_DETECTED",
            status_code=400,
            details=details
        )


class TemplateNotFoundError(AIPromptToolkitException):
    """Template not found error."""
    
    def __init__(self, template_id: str):
        super().__init__(
            message=f"Template with ID '{template_id}' not found",
            error_code="TEMPLATE_NOT_FOUND",
            status_code=404,
            details={"template_id": template_id}
        )


class ValidationError(AIPromptToolkitException):
    """Input validation errors."""

    def __init__(self, message: str, field: str = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details={**(details or {}), "field": field} if field else details
        )


class GuardrailViolation(AIPromptToolkitException):
    """Guardrail violation detected."""

    def __init__(self, message: str, violations: Optional[list] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="GUARDRAIL_VIOLATION",
            status_code=400,
            details={**(details or {}), "violations": violations or []}
        )
