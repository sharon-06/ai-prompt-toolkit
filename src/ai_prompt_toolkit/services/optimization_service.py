"""
Automated prompt optimization service.
"""

import asyncio
import random
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4
import structlog
import numpy as np
from sqlalchemy.orm import Session

from ai_prompt_toolkit.models.optimization import (
    OptimizationJobDB,
    OptimizationRequest,
    OptimizationResponse,
    OptimizationStatus,
    PromptVariant,
    PromptEvaluation,
    OptimizationTechnique,
    OptimizationConfig
)
from ai_prompt_toolkit.services.llm_factory import llm_factory
from ai_prompt_toolkit.core.config import settings
from ai_prompt_toolkit.core.exceptions import PromptOptimizationError
from ai_prompt_toolkit.utils.prompt_analyzer import PromptAnalyzer
from ai_prompt_toolkit.utils.cost_calculator import CostCalculator
from ai_prompt_toolkit.security.injection_detector import injection_detector
from ai_prompt_toolkit.security.guardrails import guardrail_engine
from ai_prompt_toolkit.security.enhanced_guardrails import enhanced_guardrail_engine, with_guardrails


class PromptOptimizer:
    """Core prompt optimization engine."""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.analyzer = PromptAnalyzer()
        self.cost_calculator = CostCalculator()
    
    async def optimize_prompt(
        self,
        db: Session,
        request: OptimizationRequest
    ) -> str:
        """Start prompt optimization job."""

        # Enhanced guardrail validation before optimization
        enhanced_result = await enhanced_guardrail_engine.validate_prompt(request.prompt)
        if not enhanced_result.is_safe:
            critical_violations = [v for v in enhanced_result.violations
                                 if v.get("severity") in ["critical", "error"]]
            if critical_violations:
                raise PromptOptimizationError(
                    f"Prompt failed enhanced guardrail validation: {len(critical_violations)} critical violations",
                    details={
                        "enhanced_guardrail_result": enhanced_result.__dict__,
                        "recommendations": enhanced_result.recommendations
                    }
                )

        # Create optimization job
        job = OptimizationJobDB(
            id=str(uuid4()),
            original_prompt=request.prompt,
            target_metrics=request.target_metrics,
            optimization_config=request.dict(),
            max_iterations=request.max_iterations,
            status=OptimizationStatus.PENDING.value
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Start optimization in background
        asyncio.create_task(self._run_optimization(db, job.id, request))
        
        return job.id
    
    async def _run_optimization(
        self,
        db: Session,
        job_id: str,
        request: OptimizationRequest
    ) -> None:
        """Run the optimization process."""
        
        try:
            # Update job status
            job = db.query(OptimizationJobDB).filter(OptimizationJobDB.id == job_id).first()
            job.status = OptimizationStatus.RUNNING.value
            db.commit()
            
            self.logger.info("Starting optimization", job_id=job_id)
            
            # Evaluate original prompt
            original_evaluation = await self._evaluate_prompt(
                request.prompt,
                request.test_cases or []
            )
            
            job.cost_original = original_evaluation.estimated_cost
            job.performance_original = original_evaluation.overall_score
            
            # Initialize optimization algorithm
            if request.use_genetic_algorithm:
                optimized_prompt, final_evaluation = await self._genetic_algorithm_optimization(
                    request.prompt,
                    request,
                    original_evaluation
                )
            else:
                optimized_prompt, final_evaluation = await self._hill_climbing_optimization(
                    request.prompt,
                    request,
                    original_evaluation
                )
            
            # Validate optimized prompt with enhanced guardrails
            optimization_validation = await enhanced_guardrail_engine.validate_optimization_request(
                request.prompt, optimized_prompt
            )

            # Update job with results
            job.optimized_prompt = optimized_prompt
            job.cost_optimized = final_evaluation.estimated_cost
            job.performance_optimized = final_evaluation.overall_score
            job.status = OptimizationStatus.COMPLETED.value
            job.completed_at = datetime.utcnow()

            # Calculate improvements
            cost_reduction = (original_evaluation.estimated_cost - final_evaluation.estimated_cost) / original_evaluation.estimated_cost
            performance_change = final_evaluation.overall_score - original_evaluation.overall_score
            
            job.results = {
                "cost_reduction": cost_reduction,
                "performance_change": performance_change,
                "original_evaluation": original_evaluation.dict(),
                "final_evaluation": final_evaluation.dict(),
                "optimization_technique": "genetic_algorithm" if request.use_genetic_algorithm else "hill_climbing",
                "guardrail_validation": {
                    "safety_maintained": optimization_validation["safety_maintained"],
                    "quality_improved": optimization_validation["quality_improved"],
                    "optimization_safe": optimization_validation["optimization_safe"],
                    "recommendations": optimization_validation["recommendations"]
                }
            }
            
            db.commit()
            
            self.logger.info(
                "Optimization completed",
                job_id=job_id,
                cost_reduction=cost_reduction,
                performance_change=performance_change
            )
            
        except Exception as e:
            # Update job with error
            job = db.query(OptimizationJobDB).filter(OptimizationJobDB.id == job_id).first()
            job.status = OptimizationStatus.FAILED.value
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
            
            self.logger.error("Optimization failed", job_id=job_id, error=str(e))
    
    async def _evaluate_prompt(
        self,
        prompt: str,
        test_cases: List[Dict[str, Any]]
    ) -> PromptEvaluation:
        """Evaluate a prompt across multiple metrics."""

        # Validate with guardrails first
        guardrail_result = guardrail_engine.validate_prompt(prompt)
        guardrail_score = 1.0 if guardrail_result["is_safe"] else 0.0

        # Analyze prompt structure
        analysis = await self.analyzer.analyze_prompt(prompt)
        
        # Calculate cost
        token_count = analysis.get("token_count", 0)
        estimated_cost = self.cost_calculator.calculate_cost(
            token_count,
            settings.default_llm_provider
        )
        
        # Run test cases if provided
        test_results = []
        if test_cases:
            for test_case in test_cases[:5]:  # Limit to 5 test cases for efficiency
                try:
                    llm = llm_factory.get_llm()
                    result = await llm.agenerate([prompt.format(**test_case.get("variables", {}))])
                    test_results.append({
                        "input": test_case,
                        "output": result.generations[0][0].text,
                        "success": True
                    })
                except Exception as e:
                    test_results.append({
                        "input": test_case,
                        "error": str(e),
                        "success": False
                    })
        
        # Calculate scores
        cost_score = max(0, 1 - (estimated_cost / 0.01))  # Normalize to 0-1
        performance_score = analysis.get("clarity_score", 0.5)
        quality_score = analysis.get("quality_score", 0.5)
        safety_score = analysis.get("safety_score", 0.8)
        latency_score = max(0, 1 - (token_count / 2000))  # Normalize based on token count
        
        # Calculate overall score (weighted average) - include guardrail score
        overall_score = (
            cost_score * 0.25 +
            performance_score * 0.25 +
            quality_score * 0.15 +
            safety_score * 0.1 +
            guardrail_score * 0.15 +  # Guardrails are important for safety
            latency_score * 0.1
        )
        
        return PromptEvaluation(
            prompt=prompt,
            cost_score=cost_score,
            performance_score=performance_score,
            quality_score=quality_score,
            safety_score=safety_score,
            latency_score=latency_score,
            overall_score=overall_score,
            test_results=test_results,
            token_count=token_count,
            estimated_cost=estimated_cost
        )

    async def _genetic_algorithm_optimization(
        self,
        original_prompt: str,
        request: OptimizationRequest,
        original_evaluation: PromptEvaluation
    ) -> Tuple[str, PromptEvaluation]:
        """Optimize prompt using genetic algorithm."""

        population_size = request.population_size
        max_generations = request.max_iterations

        # Initialize population
        population = await self._create_initial_population(original_prompt, population_size)

        best_prompt = original_prompt
        best_evaluation = original_evaluation

        for generation in range(max_generations):
            # Evaluate population
            evaluations = []
            for prompt in population:
                evaluation = await self._evaluate_prompt(prompt, request.test_cases or [])
                evaluations.append(evaluation)

            # Find best in generation
            generation_best_idx = max(range(len(evaluations)), key=lambda i: evaluations[i].overall_score)
            generation_best = evaluations[generation_best_idx]

            if generation_best.overall_score > best_evaluation.overall_score:
                best_prompt = population[generation_best_idx]
                best_evaluation = generation_best

            # Selection and reproduction
            population = await self._evolve_population(population, evaluations, request)

            self.logger.info(
                "Generation completed",
                generation=generation,
                best_score=best_evaluation.overall_score,
                cost_reduction=(original_evaluation.estimated_cost - best_evaluation.estimated_cost) / original_evaluation.estimated_cost
            )

        return best_prompt, best_evaluation

    async def _hill_climbing_optimization(
        self,
        original_prompt: str,
        request: OptimizationRequest,
        original_evaluation: PromptEvaluation
    ) -> Tuple[str, PromptEvaluation]:
        """Optimize prompt using hill climbing algorithm."""

        current_prompt = original_prompt
        current_evaluation = original_evaluation

        for iteration in range(request.max_iterations):
            # Generate neighbors
            neighbors = await self._generate_prompt_neighbors(current_prompt, 5)

            # Evaluate neighbors
            best_neighbor = current_prompt
            best_neighbor_evaluation = current_evaluation

            for neighbor in neighbors:
                evaluation = await self._evaluate_prompt(neighbor, request.test_cases or [])
                if evaluation.overall_score > best_neighbor_evaluation.overall_score:
                    best_neighbor = neighbor
                    best_neighbor_evaluation = evaluation

            # Move to best neighbor if it's better
            if best_neighbor_evaluation.overall_score > current_evaluation.overall_score:
                current_prompt = best_neighbor
                current_evaluation = best_neighbor_evaluation
            else:
                # No improvement found, stop
                break

            self.logger.info(
                "Hill climbing iteration",
                iteration=iteration,
                score=current_evaluation.overall_score
            )

        return current_prompt, current_evaluation

    async def _create_initial_population(self, original_prompt: str, size: int) -> List[str]:
        """Create initial population for genetic algorithm."""
        population = [original_prompt]

        # Generate variations
        for _ in range(size - 1):
            variant = await self._mutate_prompt(original_prompt)
            population.append(variant)

        return population

    async def _evolve_population(
        self,
        population: List[str],
        evaluations: List[PromptEvaluation],
        request: OptimizationRequest
    ) -> List[str]:
        """Evolve population using selection, crossover, and mutation."""

        # Selection (tournament selection)
        selected = []
        for _ in range(len(population)):
            tournament_size = 3
            tournament_indices = random.sample(range(len(population)), min(tournament_size, len(population)))
            winner_idx = max(tournament_indices, key=lambda i: evaluations[i].overall_score)
            selected.append(population[winner_idx])

        # Crossover and mutation
        new_population = []
        for i in range(0, len(selected), 2):
            parent1 = selected[i]
            parent2 = selected[i + 1] if i + 1 < len(selected) else selected[0]

            # Crossover
            if random.random() < 0.8:  # Crossover rate
                child1, child2 = await self._crossover_prompts(parent1, parent2)
            else:
                child1, child2 = parent1, parent2

            # Mutation
            if random.random() < 0.1:  # Mutation rate
                child1 = await self._mutate_prompt(child1)
            if random.random() < 0.1:
                child2 = await self._mutate_prompt(child2)

            new_population.extend([child1, child2])

        return new_population[:len(population)]

    async def _mutate_prompt(self, prompt: str) -> str:
        """Apply random mutations to a prompt."""
        mutations = [
            self._add_clarity_instruction,
            self._simplify_language,
            self._add_context_instruction,
            self._reorder_instructions,
            self._add_output_format,
            self._remove_redundancy
        ]

        mutation = random.choice(mutations)
        return await mutation(prompt)

    async def _crossover_prompts(self, parent1: str, parent2: str) -> Tuple[str, str]:
        """Perform crossover between two prompts."""
        # Simple sentence-level crossover
        sentences1 = parent1.split('. ')
        sentences2 = parent2.split('. ')

        # Random crossover point
        crossover_point = random.randint(1, min(len(sentences1), len(sentences2)) - 1)

        child1_sentences = sentences1[:crossover_point] + sentences2[crossover_point:]
        child2_sentences = sentences2[:crossover_point] + sentences1[crossover_point:]

        child1 = '. '.join(child1_sentences)
        child2 = '. '.join(child2_sentences)

        return child1, child2

    async def _generate_prompt_neighbors(self, prompt: str, count: int) -> List[str]:
        """Generate neighboring prompts for hill climbing."""
        neighbors = []
        for _ in range(count):
            neighbor = await self._mutate_prompt(prompt)
            neighbors.append(neighbor)
        return neighbors

    async def _add_clarity_instruction(self, prompt: str) -> str:
        """Add clarity instructions to prompt."""
        clarity_phrases = [
            "Please be clear and specific in your response.",
            "Provide a detailed and well-structured answer.",
            "Explain your reasoning step by step.",
            "Be concise but comprehensive.",
            "Use clear and simple language."
        ]
        phrase = random.choice(clarity_phrases)
        return f"{prompt}\n\n{phrase}"

    async def _simplify_language(self, prompt: str) -> str:
        """Simplify complex language in prompt."""
        # Simple word replacements
        replacements = {
            "utilize": "use",
            "demonstrate": "show",
            "facilitate": "help",
            "implement": "do",
            "subsequently": "then",
            "therefore": "so",
            "however": "but",
            "furthermore": "also"
        }

        simplified = prompt
        for complex_word, simple_word in replacements.items():
            simplified = re.sub(r'\b' + complex_word + r'\b', simple_word, simplified, flags=re.IGNORECASE)

        return simplified

    async def _add_context_instruction(self, prompt: str) -> str:
        """Add context-setting instructions."""
        context_phrases = [
            "Consider the context carefully before responding.",
            "Take into account all relevant information provided.",
            "Base your answer on the given information.",
            "Consider multiple perspectives when appropriate."
        ]
        phrase = random.choice(context_phrases)
        return f"{phrase}\n\n{prompt}"

    async def _reorder_instructions(self, prompt: str) -> str:
        """Reorder instructions in the prompt."""
        sentences = prompt.split('. ')
        if len(sentences) > 2:
            # Randomly shuffle middle sentences, keep first and last
            middle = sentences[1:-1]
            random.shuffle(middle)
            sentences = [sentences[0]] + middle + [sentences[-1]]
        return '. '.join(sentences)

    async def _add_output_format(self, prompt: str) -> str:
        """Add output format instructions."""
        format_instructions = [
            "Format your response as a numbered list.",
            "Provide your answer in bullet points.",
            "Structure your response with clear headings.",
            "Present your answer in a step-by-step format.",
            "Organize your response into clear sections."
        ]
        instruction = random.choice(format_instructions)
        return f"{prompt}\n\n{instruction}"

    async def _remove_redundancy(self, prompt: str) -> str:
        """Remove redundant phrases from prompt."""
        # Remove common redundant phrases
        redundant_patterns = [
            r'\bplease\s+please\b',
            r'\bvery\s+very\b',
            r'\breally\s+really\b',
            r'\bactually\s+actually\b'
        ]

        cleaned = prompt
        for pattern in redundant_patterns:
            cleaned = re.sub(pattern, lambda m: m.group().split()[0], cleaned, flags=re.IGNORECASE)

        return cleaned

    async def get_optimization_status(self, db: Session, job_id: str) -> OptimizationResponse:
        """Get optimization job status."""
        job = db.query(OptimizationJobDB).filter(OptimizationJobDB.id == job_id).first()

        if not job:
            raise PromptOptimizationError(f"Optimization job {job_id} not found")

        return OptimizationResponse.from_orm(job)


# Global optimizer instance
prompt_optimizer = PromptOptimizer()
