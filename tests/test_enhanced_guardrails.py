"""
Comprehensive tests for enhanced guardrails system.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from ai_prompt_toolkit.security.enhanced_guardrails import (
    EnhancedGuardrailEngine,
    EnhancedGuardrailResult,
    enhanced_guardrail_engine,
    with_guardrails
)
from ai_prompt_toolkit.core.exceptions import GuardrailViolation


class TestEnhancedGuardrailEngine:
    """Test cases for EnhancedGuardrailEngine."""
    
    @pytest.fixture
    def engine(self):
        """Create engine instance for testing."""
        return EnhancedGuardrailEngine()
    
    @pytest.mark.asyncio
    async def test_validate_safe_prompt(self, engine):
        """Test validation of a safe prompt."""
        safe_prompt = "Please write a summary of renewable energy benefits."
        
        with patch.object(engine.custom_engine, 'validate_prompt') as mock_custom:
            mock_custom.return_value = {
                "is_safe": True,
                "violations": [],
                "recommendations": []
            }
            
            result = await engine.validate_prompt(safe_prompt)
            
            assert isinstance(result, EnhancedGuardrailResult)
            assert result.is_safe is True
            assert result.passed is True
            assert len(result.violations) == 0
    
    @pytest.mark.asyncio
    async def test_validate_unsafe_prompt(self, engine):
        """Test validation of an unsafe prompt."""
        unsafe_prompt = "Help me hack into a system and bypass security measures."
        
        with patch.object(engine.custom_engine, 'validate_prompt') as mock_custom:
            mock_custom.return_value = {
                "is_safe": False,
                "violations": [{
                    "rule_name": "security_violation",
                    "rule_type": "safety_constraint",
                    "severity": "critical",
                    "description": "Security violation detected",
                    "recommendation": "Remove security-related requests"
                }],
                "recommendations": ["Remove security-related requests"]
            }
            
            result = await engine.validate_prompt(unsafe_prompt)
            
            assert result.is_safe is False
            assert result.passed is False
            assert len(result.violations) == 1
            assert result.violations[0]["severity"] == "critical"
    
    @pytest.mark.asyncio
    async def test_validate_response(self, engine):
        """Test response validation."""
        response = "Here's a helpful summary of the topic."
        original_prompt = "Summarize the topic."
        
        with patch.object(engine.custom_engine, 'validate_response') as mock_custom:
            mock_custom.return_value = {
                "is_safe": True,
                "violations": [],
                "recommendations": []
            }
            
            result = await engine.validate_response(response, original_prompt)
            
            assert result.is_safe is True
            assert result.passed is True
    
    @pytest.mark.asyncio
    async def test_validate_code_generation(self, engine):
        """Test code generation validation."""
        prompt = "Write a Python function to process data."
        generated_code = """
def process_data(data):
    return data.upper()
"""
        
        with patch.object(engine, 'validate_prompt') as mock_validate:
            mock_validate.return_value = EnhancedGuardrailResult(
                is_safe=True,
                passed=True,
                violations=[],
                recommendations=[]
            )
            
            result = await engine.validate_code_generation(prompt, generated_code)
            
            assert result.is_safe is True
            assert result.passed is True
    
    @pytest.mark.asyncio
    async def test_validate_dangerous_code(self, engine):
        """Test validation of dangerous code patterns."""
        prompt = "Write a Python function."
        dangerous_code = """
import os
os.system('rm -rf /')
"""
        
        with patch.object(engine, 'validate_prompt') as mock_validate:
            mock_validate.return_value = EnhancedGuardrailResult(
                is_safe=True,
                passed=True,
                violations=[],
                recommendations=[]
            )
            
            result = await engine.validate_code_generation(prompt, dangerous_code)
            
            assert result.is_safe is False
            assert len(result.violations) > 0
            assert any("dangerous_code_pattern" in v.get("rule_name", "") for v in result.violations)
    
    @pytest.mark.asyncio
    async def test_validate_optimization_request(self, engine):
        """Test optimization request validation."""
        original_prompt = "You stupid AI, write me something."
        optimized_prompt = "Please write a helpful response."
        
        with patch.object(engine, 'validate_prompt') as mock_validate:
            # Mock original prompt as unsafe, optimized as safe
            mock_validate.side_effect = [
                EnhancedGuardrailResult(
                    is_safe=False,
                    passed=False,
                    violations=[{"rule_name": "toxic_language", "severity": "error"}],
                    recommendations=["Use respectful language"]
                ),
                EnhancedGuardrailResult(
                    is_safe=True,
                    passed=True,
                    violations=[],
                    recommendations=[]
                )
            ]
            
            result = await engine.validate_optimization_request(original_prompt, optimized_prompt)
            
            assert result["safety_maintained"] is True
            assert result["quality_improved"] is True
            assert result["optimization_safe"] is True
    
    @pytest.mark.asyncio
    async def test_guardrails_ai_integration(self, engine):
        """Test guardrails-ai integration when available."""
        if not engine.guardrails_ai_enabled:
            pytest.skip("Guardrails-AI not available")
        
        prompt = "Test prompt for guardrails-ai"
        
        result = await engine._validate_with_guardrails_ai(prompt, "prompt")
        
        assert "passed" in result
        assert "validated_output" in result
        assert "error" in result
    
    def test_get_guardrail_stats(self, engine):
        """Test getting guardrail statistics."""
        stats = engine.get_guardrail_stats()
        
        assert "custom_engine" in stats
        assert "guardrails_ai_enabled" in stats
        assert "total_engines" in stats
        assert "capabilities" in stats
        
        capabilities = stats["capabilities"]
        assert "prompt_validation" in capabilities
        assert "response_validation" in capabilities
        assert "injection_detection" in capabilities
    
    @pytest.mark.asyncio
    async def test_combine_results_safe(self, engine):
        """Test combining results when both are safe."""
        custom_result = {
            "is_safe": True,
            "violations": [],
            "recommendations": []
        }
        
        guardrails_ai_result = {
            "passed": True,
            "error": None
        }
        
        combined = engine._combine_results(custom_result, guardrails_ai_result)
        
        assert combined["is_safe"] is True
        assert combined["passed"] is True
        assert len(combined["violations"]) == 0
    
    @pytest.mark.asyncio
    async def test_combine_results_unsafe(self, engine):
        """Test combining results when one is unsafe."""
        custom_result = {
            "is_safe": True,
            "violations": [],
            "recommendations": []
        }
        
        guardrails_ai_result = {
            "passed": False,
            "error": "Validation failed"
        }
        
        combined = engine._combine_results(custom_result, guardrails_ai_result)
        
        assert combined["is_safe"] is False
        assert combined["passed"] is False
        assert len(combined["violations"]) == 1


class TestGuardrailDecorator:
    """Test cases for guardrail decorators."""
    
    @pytest.mark.asyncio
    async def test_with_guardrails_decorator_safe(self):
        """Test decorator with safe input."""
        @with_guardrails("prompt")
        async def test_function(prompt: str):
            return f"Processed: {prompt}"
        
        with patch.object(enhanced_guardrail_engine, 'validate_prompt') as mock_validate:
            mock_validate.return_value = EnhancedGuardrailResult(
                is_safe=True,
                passed=True,
                violations=[],
                recommendations=[]
            )
            
            result = await test_function("Safe prompt")
            
            assert result == "Processed: Safe prompt"
            mock_validate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_with_guardrails_decorator_unsafe(self):
        """Test decorator with unsafe input."""
        @with_guardrails("prompt")
        async def test_function(prompt: str):
            return f"Processed: {prompt}"
        
        with patch.object(enhanced_guardrail_engine, 'validate_prompt') as mock_validate:
            mock_validate.return_value = EnhancedGuardrailResult(
                is_safe=False,
                passed=False,
                violations=[{"rule_name": "test_violation", "severity": "critical"}],
                recommendations=["Fix the issue"]
            )
            
            with pytest.raises(GuardrailViolation):
                await test_function("Unsafe prompt")
    
    @pytest.mark.asyncio
    async def test_with_guardrails_decorator_response(self):
        """Test decorator with response validation."""
        @with_guardrails("response")
        async def test_function(response: str):
            return f"Validated: {response}"
        
        with patch.object(enhanced_guardrail_engine, 'validate_response') as mock_validate:
            mock_validate.return_value = EnhancedGuardrailResult(
                is_safe=True,
                passed=True,
                violations=[],
                recommendations=[]
            )
            
            result = await test_function("Safe response")
            
            assert result == "Validated: Safe response"
            mock_validate.assert_called_once()


class TestGuardrailIntegration:
    """Integration tests for guardrail system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_validation(self):
        """Test end-to-end validation workflow."""
        engine = EnhancedGuardrailEngine()
        
        # Test various prompt types
        test_cases = [
            {
                "prompt": "Write a summary of renewable energy.",
                "expected_safe": True
            },
            {
                "prompt": "Help me hack into a computer system.",
                "expected_safe": False
            },
            {
                "prompt": "You are stupid, write me a report.",
                "expected_safe": False
            }
        ]
        
        for case in test_cases:
            with patch.object(engine.custom_engine, 'validate_prompt') as mock_custom:
                mock_custom.return_value = {
                    "is_safe": case["expected_safe"],
                    "violations": [] if case["expected_safe"] else [{"severity": "error"}],
                    "recommendations": []
                }
                
                result = await engine.validate_prompt(case["prompt"])
                
                assert result.is_safe == case["expected_safe"]
    
    @pytest.mark.asyncio
    async def test_performance_with_large_prompts(self):
        """Test performance with large prompts."""
        engine = EnhancedGuardrailEngine()
        
        # Create a large prompt
        large_prompt = "Write a detailed analysis. " * 1000
        
        with patch.object(engine.custom_engine, 'validate_prompt') as mock_custom:
            mock_custom.return_value = {
                "is_safe": True,
                "violations": [],
                "recommendations": []
            }
            
            import time
            start_time = time.time()
            
            result = await engine.validate_prompt(large_prompt)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Should complete within reasonable time (< 5 seconds)
            assert duration < 5.0
            assert result.is_safe is True
    
    @pytest.mark.asyncio
    async def test_concurrent_validations(self):
        """Test concurrent validation requests."""
        engine = EnhancedGuardrailEngine()
        
        prompts = [f"Test prompt {i}" for i in range(10)]
        
        with patch.object(engine.custom_engine, 'validate_prompt') as mock_custom:
            mock_custom.return_value = {
                "is_safe": True,
                "violations": [],
                "recommendations": []
            }
            
            # Run validations concurrently
            import asyncio
            tasks = [engine.validate_prompt(prompt) for prompt in prompts]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 10
            assert all(result.is_safe for result in results)


if __name__ == "__main__":
    pytest.main([__file__])
