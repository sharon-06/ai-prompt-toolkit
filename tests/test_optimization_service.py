"""
Comprehensive tests for the optimization service.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from ai_prompt_toolkit.services.optimization_service import PromptOptimizer
from ai_prompt_toolkit.models.optimization import OptimizationRequest, OptimizationStatus
from ai_prompt_toolkit.core.exceptions import PromptOptimizationError


class TestPromptOptimizer:
    """Test cases for PromptOptimizer."""
    
    @pytest.fixture
    def optimizer(self):
        """Create optimizer instance for testing."""
        return PromptOptimizer()
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = Mock()
        db.add = Mock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.query = Mock()
        return db
    
    @pytest.fixture
    def sample_request(self):
        """Sample optimization request."""
        return OptimizationRequest(
            prompt="Write a detailed summary of the following text with comprehensive analysis and insights: {text}",
            max_iterations=3,
            use_genetic_algorithm=True,
            target_cost_reduction=0.3,
            target_quality_threshold=0.8
        )
    
    @pytest.mark.asyncio
    async def test_optimize_prompt_success(self, optimizer, mock_db, sample_request):
        """Test successful prompt optimization."""
        with patch('ai_prompt_toolkit.services.optimization_service.enhanced_guardrail_engine') as mock_guardrails:
            # Mock guardrail validation
            mock_guardrails.validate_prompt.return_value = Mock(
                is_safe=True,
                violations=[],
                recommendations=[]
            )
            mock_guardrails.validate_optimization_request.return_value = {
                "safety_maintained": True,
                "quality_improved": True,
                "optimization_safe": True,
                "recommendations": ["Optimization successful"]
            }
            
            # Mock database query
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            with patch.object(optimizer, '_run_optimization') as mock_run:
                mock_run.return_value = (
                    "Summarize the following text: {text}",
                    Mock(overall_score=0.9, estimated_cost=0.05),
                    Mock(overall_score=0.7, estimated_cost=0.08)
                )
                
                job_id = await optimizer.optimize_prompt(mock_db, sample_request)
                
                assert job_id is not None
                assert len(job_id) > 0
                mock_guardrails.validate_prompt.assert_called_once()
                mock_run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_optimize_prompt_guardrail_failure(self, optimizer, mock_db, sample_request):
        """Test optimization failure due to guardrail violations."""
        with patch('ai_prompt_toolkit.services.optimization_service.enhanced_guardrail_engine') as mock_guardrails:
            # Mock guardrail validation failure
            mock_guardrails.validate_prompt.return_value = Mock(
                is_safe=False,
                violations=[{
                    "severity": "critical",
                    "rule_name": "harmful_content",
                    "description": "Harmful content detected"
                }],
                recommendations=["Remove harmful content"]
            )
            
            with pytest.raises(PromptOptimizationError) as exc_info:
                await optimizer.optimize_prompt(mock_db, sample_request)
            
            assert "critical violations" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_optimization_status_completed(self, optimizer, mock_db):
        """Test getting status of completed optimization."""
        # Mock completed job
        mock_job = Mock()
        mock_job.id = "test-job-id"
        mock_job.status = OptimizationStatus.COMPLETED.value
        mock_job.optimized_prompt = "Optimized prompt"
        mock_job.cost_original = 0.10
        mock_job.cost_optimized = 0.05
        mock_job.performance_original = 0.7
        mock_job.performance_optimized = 0.9
        mock_job.results = {
            "cost_reduction": 0.5,
            "performance_change": 0.2,
            "guardrail_validation": {
                "safety_maintained": True,
                "optimization_safe": True
            }
        }
        mock_job.created_at = datetime.utcnow()
        mock_job.completed_at = datetime.utcnow()
        mock_job.error_message = None
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job
        
        result = await optimizer.get_optimization_status(mock_db, "test-job-id")
        
        assert result.job_id == "test-job-id"
        assert result.status == "completed"
        assert result.optimized_prompt == "Optimized prompt"
        assert result.cost_reduction == 0.5
    
    @pytest.mark.asyncio
    async def test_get_optimization_status_not_found(self, optimizer, mock_db):
        """Test getting status of non-existent job."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(PromptOptimizationError) as exc_info:
            await optimizer.get_optimization_status(mock_db, "non-existent-job")
        
        assert "not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_genetic_algorithm_optimization(self, optimizer):
        """Test genetic algorithm optimization strategy."""
        prompt = "Write a very long and detailed explanation about {topic} with extensive background information"
        
        with patch.object(optimizer, '_evaluate_prompt') as mock_evaluate:
            mock_evaluate.return_value = Mock(overall_score=0.8, estimated_cost=0.05)
            
            result = await optimizer._run_genetic_algorithm(prompt, max_iterations=2)
            
            assert result is not None
            assert len(result) > 0
            assert len(result) < len(prompt)  # Should be shorter
    
    @pytest.mark.asyncio
    async def test_hill_climbing_optimization(self, optimizer):
        """Test hill climbing optimization strategy."""
        prompt = "Please write a comprehensive and detailed analysis of {data} with thorough examination"
        
        with patch.object(optimizer, '_evaluate_prompt') as mock_evaluate:
            mock_evaluate.return_value = Mock(overall_score=0.8, estimated_cost=0.05)
            
            result = await optimizer._run_hill_climbing(prompt, max_iterations=2)
            
            assert result is not None
            assert len(result) > 0
    
    def test_generate_variations(self, optimizer):
        """Test prompt variation generation."""
        prompt = "Write a detailed summary of {text}"
        
        variations = optimizer._generate_variations(prompt)
        
        assert len(variations) > 0
        assert all(isinstance(v, str) for v in variations)
        assert all(len(v) > 0 for v in variations)
    
    def test_crossover_prompts(self, optimizer):
        """Test prompt crossover operation."""
        parent1 = "Write a summary of {text}"
        parent2 = "Create a brief overview of {text}"
        
        child = optimizer._crossover_prompts(parent1, parent2)
        
        assert isinstance(child, str)
        assert len(child) > 0
        assert "{text}" in child
    
    def test_mutate_prompt(self, optimizer):
        """Test prompt mutation operation."""
        prompt = "Write a detailed summary of {text}"
        
        mutated = optimizer._mutate_prompt(prompt)
        
        assert isinstance(mutated, str)
        assert len(mutated) > 0
        # Mutation might change the prompt
    
    @pytest.mark.asyncio
    async def test_evaluate_prompt(self, optimizer):
        """Test prompt evaluation."""
        prompt = "Summarize {text}"
        
        with patch('ai_prompt_toolkit.services.optimization_service.PromptAnalyzer') as mock_analyzer:
            mock_analyzer.return_value.analyze_prompt.return_value = {
                "quality_score": 0.8,
                "clarity_score": 0.9,
                "safety_score": 1.0,
                "token_count": 50
            }
            
            with patch('ai_prompt_toolkit.services.optimization_service.CostCalculator') as mock_calculator:
                mock_calculator.return_value.calculate_cost.return_value = 0.05
                
                evaluation = await optimizer._evaluate_prompt(prompt)
                
                assert evaluation.overall_score > 0
                assert evaluation.estimated_cost > 0
    
    def test_optimization_techniques_coverage(self, optimizer):
        """Test that all optimization techniques are implemented."""
        techniques = [
            'remove_redundancy',
            'simplify_language',
            'add_structure',
            'optimize_instructions',
            'reduce_verbosity'
        ]
        
        for technique in techniques:
            method_name = f'_apply_{technique}'
            assert hasattr(optimizer, method_name), f"Missing technique: {technique}"
    
    @pytest.mark.asyncio
    async def test_concurrent_optimizations(self, optimizer, mock_db):
        """Test handling multiple concurrent optimizations."""
        requests = [
            OptimizationRequest(
                prompt=f"Test prompt {i}",
                max_iterations=1,
                use_genetic_algorithm=True
            ) for i in range(3)
        ]
        
        with patch('ai_prompt_toolkit.services.optimization_service.enhanced_guardrail_engine') as mock_guardrails:
            mock_guardrails.validate_prompt.return_value = Mock(
                is_safe=True,
                violations=[],
                recommendations=[]
            )
            mock_guardrails.validate_optimization_request.return_value = {
                "safety_maintained": True,
                "quality_improved": True,
                "optimization_safe": True,
                "recommendations": []
            }
            
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            with patch.object(optimizer, '_run_optimization') as mock_run:
                mock_run.return_value = (
                    "Optimized prompt",
                    Mock(overall_score=0.9, estimated_cost=0.05),
                    Mock(overall_score=0.7, estimated_cost=0.08)
                )
                
                # Run optimizations concurrently
                tasks = [optimizer.optimize_prompt(mock_db, req) for req in requests]
                job_ids = await asyncio.gather(*tasks)
                
                assert len(job_ids) == 3
                assert all(job_id for job_id in job_ids)
    
    @pytest.mark.asyncio
    async def test_optimization_with_custom_parameters(self, optimizer, mock_db):
        """Test optimization with custom parameters."""
        request = OptimizationRequest(
            prompt="Custom test prompt",
            max_iterations=10,
            use_genetic_algorithm=False,  # Use hill climbing
            target_cost_reduction=0.5,
            target_quality_threshold=0.9
        )
        
        with patch('ai_prompt_toolkit.services.optimization_service.enhanced_guardrail_engine') as mock_guardrails:
            mock_guardrails.validate_prompt.return_value = Mock(
                is_safe=True,
                violations=[],
                recommendations=[]
            )
            mock_guardrails.validate_optimization_request.return_value = {
                "safety_maintained": True,
                "quality_improved": True,
                "optimization_safe": True,
                "recommendations": []
            }
            
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            with patch.object(optimizer, '_run_optimization') as mock_run:
                mock_run.return_value = (
                    "Optimized prompt",
                    Mock(overall_score=0.95, estimated_cost=0.03),
                    Mock(overall_score=0.8, estimated_cost=0.06)
                )
                
                job_id = await optimizer.optimize_prompt(mock_db, request)
                
                assert job_id is not None
                # Verify hill climbing was used (not genetic algorithm)
                mock_run.assert_called_once()
                args, kwargs = mock_run.call_args
                assert not kwargs.get('use_genetic_algorithm', True)


if __name__ == "__main__":
    pytest.main([__file__])
