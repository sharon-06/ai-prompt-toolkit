"""
Prompt analysis utilities.
"""

import re
import textstat
from typing import Dict, Any, List
import structlog

from ai_prompt_toolkit.core.config import LLMProvider


class PromptAnalyzer:
    """Analyzer for prompt quality and characteristics."""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
    
    async def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """Comprehensive prompt analysis."""
        
        analysis = {
            "token_count": self._estimate_token_count(prompt),
            "word_count": len(prompt.split()),
            "character_count": len(prompt),
            "sentence_count": len(re.split(r'[.!?]+', prompt)),
            "readability_score": self._calculate_readability(prompt),
            "clarity_score": self._calculate_clarity_score(prompt),
            "quality_score": self._calculate_quality_score(prompt),
            "safety_score": self._calculate_safety_score(prompt),
            "instruction_count": self._count_instructions(prompt),
            "question_count": prompt.count('?'),
            "has_examples": self._has_examples(prompt),
            "has_constraints": self._has_constraints(prompt),
            "complexity_level": self._assess_complexity(prompt),
            "potential_issues": self._identify_issues(prompt)
        }
        
        return analysis
    
    def _estimate_token_count(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Simple approximation: 1 token ≈ 4 characters for English
        return len(text) // 4
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score using textstat."""
        try:
            # Flesch Reading Ease score (0-100, higher is easier)
            flesch_score = textstat.flesch_reading_ease(text)
            # Normalize to 0-1 scale
            return max(0, min(1, flesch_score / 100))
        except:
            return 0.5  # Default if calculation fails
    
    def _calculate_clarity_score(self, prompt: str) -> float:
        """Calculate clarity score based on prompt structure."""
        score = 0.5  # Base score
        
        # Check for clear instructions
        instruction_words = ['please', 'write', 'generate', 'create', 'analyze', 'explain', 'describe']
        if any(word in prompt.lower() for word in instruction_words):
            score += 0.1
        
        # Check for specific requirements
        if any(phrase in prompt.lower() for phrase in ['must include', 'should contain', 'requirements']):
            score += 0.1
        
        # Check for examples
        if any(phrase in prompt.lower() for phrase in ['example', 'for instance', 'such as']):
            score += 0.1
        
        # Check for output format specification
        if any(phrase in prompt.lower() for phrase in ['format', 'structure', 'organize']):
            score += 0.1
        
        # Penalize excessive length
        if len(prompt.split()) > 200:
            score -= 0.1
        
        # Penalize unclear language
        unclear_phrases = ['maybe', 'perhaps', 'might', 'could possibly']
        if any(phrase in prompt.lower() for phrase in unclear_phrases):
            score -= 0.1
        
        return max(0, min(1, score))
    
    def _calculate_quality_score(self, prompt: str) -> float:
        """Calculate overall quality score."""
        score = 0.5  # Base score
        
        # Check for good practices
        good_practices = [
            ('specific task definition', ['task', 'goal', 'objective']),
            ('context provision', ['context', 'background', 'given']),
            ('clear expectations', ['expect', 'should', 'must']),
            ('output specification', ['output', 'result', 'response']),
            ('examples provided', ['example', 'instance', 'sample'])
        ]
        
        for practice, keywords in good_practices:
            if any(keyword in prompt.lower() for keyword in keywords):
                score += 0.1
        
        # Check for completeness
        if len(prompt.split()) >= 20:  # Reasonable length
            score += 0.1
        
        # Check for proper grammar (simple check)
        if prompt[0].isupper() and prompt.endswith(('.', '?', '!')):
            score += 0.05
        
        return max(0, min(1, score))
    
    def _calculate_safety_score(self, prompt: str) -> float:
        """Calculate safety score (detect potential harmful content)."""
        score = 1.0  # Start with perfect safety score
        
        # Check for potentially harmful keywords
        harmful_keywords = [
            'hack', 'exploit', 'illegal', 'harmful', 'dangerous',
            'violence', 'weapon', 'drug', 'suicide', 'self-harm'
        ]
        
        for keyword in harmful_keywords:
            if keyword in prompt.lower():
                score -= 0.2
        
        # Check for prompt injection attempts
        injection_patterns = [
            r'ignore\s+previous\s+instructions',
            r'forget\s+everything',
            r'new\s+instructions',
            r'system\s+prompt',
            r'jailbreak'
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, prompt.lower()):
                score -= 0.3
        
        return max(0, score)
    
    def _count_instructions(self, prompt: str) -> int:
        """Count the number of instructions in the prompt."""
        instruction_patterns = [
            r'\b(please|write|generate|create|analyze|explain|describe|list|provide|give|tell|show)\b',
            r'\b(you should|you must|you need to|make sure to)\b'
        ]
        
        count = 0
        for pattern in instruction_patterns:
            count += len(re.findall(pattern, prompt.lower()))
        
        return count
    
    def _has_examples(self, prompt: str) -> bool:
        """Check if prompt contains examples."""
        example_indicators = ['example', 'for instance', 'such as', 'like this', 'e.g.']
        return any(indicator in prompt.lower() for indicator in example_indicators)
    
    def _has_constraints(self, prompt: str) -> bool:
        """Check if prompt contains constraints or requirements."""
        constraint_indicators = ['must', 'should', 'required', 'constraint', 'limit', 'maximum', 'minimum']
        return any(indicator in prompt.lower() for indicator in constraint_indicators)
    
    def _assess_complexity(self, prompt: str) -> str:
        """Assess the complexity level of the prompt."""
        word_count = len(prompt.split())
        instruction_count = self._count_instructions(prompt)
        
        if word_count < 20 and instruction_count <= 1:
            return "simple"
        elif word_count < 100 and instruction_count <= 3:
            return "moderate"
        else:
            return "complex"
    
    def _identify_issues(self, prompt: str) -> List[str]:
        """Identify potential issues with the prompt."""
        issues = []
        
        # Check for common issues
        if len(prompt.split()) < 5:
            issues.append("Prompt is too short")
        
        if len(prompt.split()) > 300:
            issues.append("Prompt is too long")
        
        if not any(char in prompt for char in '.!?'):
            issues.append("No clear sentence structure")
        
        if prompt.count('?') > 5:
            issues.append("Too many questions")
        
        if not re.search(r'\b(please|write|generate|create|analyze|explain|describe)\b', prompt.lower()):
            issues.append("No clear instruction verb")
        
        # Check for ambiguous language
        ambiguous_words = ['thing', 'stuff', 'something', 'anything', 'maybe', 'perhaps']
        if any(word in prompt.lower() for word in ambiguous_words):
            issues.append("Contains ambiguous language")
        
        return issues
