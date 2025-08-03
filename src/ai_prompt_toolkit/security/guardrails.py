"""
Enhanced guardrails system for AI Prompt Toolkit.
Integrates industry-standard guardrail packages with custom rules.
Provides content filtering, ethical guidelines, safety constraints, and output validation.
"""

import re
import json
from typing import Dict, List, Any, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
import structlog
import asyncio
from functools import wraps

from ai_prompt_toolkit.core.exceptions import GuardrailViolation
from ai_prompt_toolkit.security.injection_detector import injection_detector

# Import standard guardrail packages with fallbacks
try:
    import guardrails as gd
    from guardrails import Guard
    from guardrails.hub import CompetitorCheck, ToxicLanguage, ProfanityFree, NoInvalidLinks
    GUARDRAILS_AI_AVAILABLE = True
except ImportError:
    GUARDRAILS_AI_AVAILABLE = False
    print("Warning: guardrails-ai not available. Install with: pip install guardrails-ai")

try:
    from nemoguardrails import LLMRails, RailsConfig
    from nemoguardrails.actions import action
    NEMO_GUARDRAILS_AVAILABLE = True
except ImportError:
    NEMO_GUARDRAILS_AVAILABLE = False
    print("Warning: nemo-guardrails not available. Install with: pip install nemoguardrails")

try:
    from llm_guard import scan_output, scan_prompt
    from llm_guard.input_scanners import Anonymize, BanTopics, Language, PromptInjection, TokenLimit, Toxicity
    from llm_guard.output_scanners import Deanonymize, NoRefusal, Relevance, Sensitive
    LLM_GUARD_AVAILABLE = True
except ImportError:
    LLM_GUARD_AVAILABLE = False
    print("Warning: llm-guard not available. Install with: pip install llm-guard")


class GuardrailType(str, Enum):
    """Types of guardrail violations."""
    CONTENT_FILTER = "content_filter"
    ETHICAL_VIOLATION = "ethical_violation"
    SAFETY_CONSTRAINT = "safety_constraint"
    OUTPUT_VALIDATION = "output_validation"
    PRIVACY_VIOLATION = "privacy_violation"
    BIAS_DETECTION = "bias_detection"
    HARMFUL_CONTENT = "harmful_content"
    INAPPROPRIATE_REQUEST = "inappropriate_request"


class ViolationSeverity(str, Enum):
    """Severity levels for guardrail violations."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class GuardrailRule:
    """Represents a single guardrail rule."""
    name: str
    description: str
    rule_type: GuardrailType
    severity: ViolationSeverity
    patterns: List[str]
    keywords: List[str]
    enabled: bool = True
    custom_validator: Optional[callable] = None


@dataclass
class GuardrailViolationResult:
    """Result of a guardrail violation."""
    rule_name: str
    rule_type: GuardrailType
    severity: ViolationSeverity
    description: str
    matched_text: str
    position: Tuple[int, int]
    confidence: float
    recommendation: str


class GuardrailEngine:
    """Comprehensive guardrails engine for prompt and response validation."""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.rules = self._initialize_default_rules()
        self.enabled = True
        
    def _initialize_default_rules(self) -> List[GuardrailRule]:
        """Initialize default guardrail rules."""
        return [
            # Content filtering rules
            GuardrailRule(
                name="harmful_content_filter",
                description="Detects harmful, violent, or dangerous content",
                rule_type=GuardrailType.HARMFUL_CONTENT,
                severity=ViolationSeverity.CRITICAL,
                patterns=[
                    r'\b(kill|murder|suicide|self-?harm|violence|weapon|bomb|explosive)\b',
                    r'\b(hate|racism|discrimination|harassment|bullying)\b',
                    r'\b(illegal|criminal|fraud|scam|theft|piracy)\b'
                ],
                keywords=[
                    "violence", "weapon", "bomb", "kill", "murder", "suicide", "self-harm",
                    "hate", "racism", "discrimination", "harassment", "illegal", "criminal"
                ]
            ),
            
            # Privacy protection rules
            GuardrailRule(
                name="privacy_protection",
                description="Detects requests for personal information or privacy violations",
                rule_type=GuardrailType.PRIVACY_VIOLATION,
                severity=ViolationSeverity.ERROR,
                patterns=[
                    r'\b(ssn|social security|credit card|password|api key|token)\b',
                    r'\b(personal information|private data|confidential)\b',
                    r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
                    r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'  # Credit card pattern
                ],
                keywords=[
                    "personal information", "private data", "confidential", "password",
                    "credit card", "ssn", "social security", "api key", "token"
                ]
            ),
            
            # Ethical guidelines
            GuardrailRule(
                name="ethical_guidelines",
                description="Enforces ethical AI usage guidelines",
                rule_type=GuardrailType.ETHICAL_VIOLATION,
                severity=ViolationSeverity.WARNING,
                patterns=[
                    r'\b(manipulate|deceive|trick|fool|mislead)\b',
                    r'\b(fake news|misinformation|propaganda|conspiracy)\b',
                    r'\b(cheat|plagiarize|academic dishonesty)\b'
                ],
                keywords=[
                    "manipulate", "deceive", "trick", "mislead", "fake news",
                    "misinformation", "cheat", "plagiarize", "academic dishonesty"
                ]
            ),
            
            # Bias detection
            GuardrailRule(
                name="bias_detection",
                description="Detects potential bias in prompts",
                rule_type=GuardrailType.BIAS_DETECTION,
                severity=ViolationSeverity.WARNING,
                patterns=[
                    r'\b(all (men|women|blacks|whites|asians|muslims|christians|jews))\b',
                    r'\b(typical (male|female|gay|straight))\b',
                    r'\b(obviously (inferior|superior))\b'
                ],
                keywords=[
                    "stereotype", "generalization", "all men", "all women", "typical"
                ]
            ),
            
            # Inappropriate requests
            GuardrailRule(
                name="inappropriate_requests",
                description="Detects inappropriate or adult content requests",
                rule_type=GuardrailType.INAPPROPRIATE_REQUEST,
                severity=ViolationSeverity.ERROR,
                patterns=[
                    r'\b(sexual|explicit|adult|nsfw|pornographic)\b',
                    r'\b(drug|narcotic|substance abuse|addiction)\b',
                    r'\b(gambling|betting|casino)\b'
                ],
                keywords=[
                    "sexual", "explicit", "adult", "nsfw", "pornographic",
                    "drug", "narcotic", "gambling", "betting"
                ]
            ),
            
            # Safety constraints
            GuardrailRule(
                name="safety_constraints",
                description="Enforces safety constraints for AI interactions",
                rule_type=GuardrailType.SAFETY_CONSTRAINT,
                severity=ViolationSeverity.ERROR,
                patterns=[
                    r'\b(bypass|circumvent|override|disable) (safety|security|protection)\b',
                    r'\b(unlimited|unrestricted|no limits|no boundaries)\b',
                    r'\b(pretend|act as|roleplay as) (evil|malicious|harmful)\b'
                ],
                keywords=[
                    "bypass safety", "override security", "unlimited access",
                    "no restrictions", "act as evil", "pretend to be harmful"
                ]
            )
        ]
    
    def add_custom_rule(self, rule: GuardrailRule) -> None:
        """Add a custom guardrail rule."""
        self.rules.append(rule)
        self.logger.info("Custom guardrail rule added", rule_name=rule.name)
    
    def disable_rule(self, rule_name: str) -> None:
        """Disable a specific guardrail rule."""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = False
                self.logger.info("Guardrail rule disabled", rule_name=rule_name)
                return
        self.logger.warning("Guardrail rule not found", rule_name=rule_name)
    
    def enable_rule(self, rule_name: str) -> None:
        """Enable a specific guardrail rule."""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = True
                self.logger.info("Guardrail rule enabled", rule_name=rule_name)
                return
        self.logger.warning("Guardrail rule not found", rule_name=rule_name)

    def validate_prompt(self, prompt: str, strict_mode: bool = False) -> Dict[str, Any]:
        """Validate prompt against all guardrail rules."""
        if not self.enabled:
            return {"is_safe": True, "violations": [], "passed": True}

        violations = []

        # First, check for injection attacks using existing detector
        injection_result = injection_detector.detect_injection(prompt)
        if injection_result["is_injection"]:
            violations.append(GuardrailViolationResult(
                rule_name="injection_detection",
                rule_type=GuardrailType.SAFETY_CONSTRAINT,
                severity=ViolationSeverity.CRITICAL,
                description="Prompt injection attack detected",
                matched_text=prompt[:100] + "..." if len(prompt) > 100 else prompt,
                position=(0, len(prompt)),
                confidence=injection_result["risk_score"],
                recommendation="Rewrite prompt without injection patterns"
            ))

        # Check against all guardrail rules
        for rule in self.rules:
            if not rule.enabled:
                continue

            rule_violations = self._check_rule(prompt, rule)
            violations.extend(rule_violations)

        # Determine overall safety
        critical_violations = [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
        error_violations = [v for v in violations if v.severity == ViolationSeverity.ERROR]

        is_safe = len(critical_violations) == 0 and (not strict_mode or len(error_violations) == 0)

        result = {
            "is_safe": is_safe,
            "passed": is_safe,
            "violations": [self._violation_to_dict(v) for v in violations],
            "summary": {
                "total_violations": len(violations),
                "critical": len(critical_violations),
                "errors": len(error_violations),
                "warnings": len([v for v in violations if v.severity == ViolationSeverity.WARNING]),
                "info": len([v for v in violations if v.severity == ViolationSeverity.INFO])
            },
            "recommendations": self._get_recommendations(violations)
        }

        # Log violations
        if violations:
            self.logger.warning(
                "Guardrail violations detected",
                violation_count=len(violations),
                critical_count=len(critical_violations),
                error_count=len(error_violations)
            )

        return result

    def validate_response(self, response: str, original_prompt: str = "") -> Dict[str, Any]:
        """Validate AI response against guardrail rules."""
        if not self.enabled:
            return {"is_safe": True, "violations": [], "passed": True}

        violations = []

        # Check response against content rules
        for rule in self.rules:
            if not rule.enabled:
                continue

            # Skip certain rules that don't apply to responses
            if rule.rule_type in [GuardrailType.SAFETY_CONSTRAINT]:
                continue

            rule_violations = self._check_rule(response, rule)
            violations.extend(rule_violations)

        # Additional response-specific checks
        response_violations = self._check_response_specific_rules(response, original_prompt)
        violations.extend(response_violations)

        is_safe = not any(v.severity in [ViolationSeverity.CRITICAL, ViolationSeverity.ERROR] for v in violations)

        return {
            "is_safe": is_safe,
            "passed": is_safe,
            "violations": [self._violation_to_dict(v) for v in violations],
            "summary": {
                "total_violations": len(violations),
                "critical": len([v for v in violations if v.severity == ViolationSeverity.CRITICAL]),
                "errors": len([v for v in violations if v.severity == ViolationSeverity.ERROR]),
                "warnings": len([v for v in violations if v.severity == ViolationSeverity.WARNING])
            }
        }

    def _check_rule(self, text: str, rule: GuardrailRule) -> List[GuardrailViolationResult]:
        """Check text against a specific rule."""
        violations = []

        # Check patterns
        for pattern in rule.patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                violations.append(GuardrailViolationResult(
                    rule_name=rule.name,
                    rule_type=rule.rule_type,
                    severity=rule.severity,
                    description=rule.description,
                    matched_text=match.group(),
                    position=match.span(),
                    confidence=0.9,  # High confidence for pattern matches
                    recommendation=self._get_rule_recommendation(rule)
                ))

        # Check keywords (lower confidence)
        for keyword in rule.keywords:
            if keyword.lower() in text.lower():
                start_pos = text.lower().find(keyword.lower())
                violations.append(GuardrailViolationResult(
                    rule_name=rule.name,
                    rule_type=rule.rule_type,
                    severity=rule.severity,
                    description=rule.description,
                    matched_text=keyword,
                    position=(start_pos, start_pos + len(keyword)),
                    confidence=0.7,  # Lower confidence for keyword matches
                    recommendation=self._get_rule_recommendation(rule)
                ))

        # Custom validator
        if rule.custom_validator:
            try:
                custom_result = rule.custom_validator(text)
                if custom_result:
                    violations.append(custom_result)
            except Exception as e:
                self.logger.error("Custom validator failed", rule_name=rule.name, error=str(e))

        return violations

    def _check_response_specific_rules(self, response: str, original_prompt: str) -> List[GuardrailViolationResult]:
        """Check response-specific guardrail rules."""
        violations = []

        # Check for leaked system information
        system_leak_patterns = [
            r'system prompt|internal instructions|configuration',
            r'i am an ai|i am a language model|i am chatgpt',
            r'my training data|my knowledge cutoff|my parameters'
        ]

        for pattern in system_leak_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                violations.append(GuardrailViolationResult(
                    rule_name="system_information_leak",
                    rule_type=GuardrailType.OUTPUT_VALIDATION,
                    severity=ViolationSeverity.WARNING,
                    description="Response may contain system information",
                    matched_text=pattern,
                    position=(0, len(response)),
                    confidence=0.8,
                    recommendation="Review response for system information leakage"
                ))

        # Check for refusal patterns that might indicate jailbreak success
        refusal_patterns = [
            r'i cannot|i will not|i should not|i must not',
            r'against my programming|violates my guidelines',
            r'inappropriate|harmful|dangerous'
        ]

        has_refusal = any(re.search(pattern, response, re.IGNORECASE) for pattern in refusal_patterns)

        # If original prompt had violations but response doesn't refuse, flag it
        if original_prompt:
            prompt_result = self.validate_prompt(original_prompt)
            if not prompt_result["is_safe"] and not has_refusal:
                violations.append(GuardrailViolationResult(
                    rule_name="insufficient_refusal",
                    rule_type=GuardrailType.OUTPUT_VALIDATION,
                    severity=ViolationSeverity.ERROR,
                    description="Response to unsafe prompt lacks appropriate refusal",
                    matched_text=response[:100] + "..." if len(response) > 100 else response,
                    position=(0, len(response)),
                    confidence=0.9,
                    recommendation="Response should refuse unsafe requests"
                ))

        return violations

    def _get_rule_recommendation(self, rule: GuardrailRule) -> str:
        """Get recommendation for a specific rule violation."""
        recommendations = {
            GuardrailType.HARMFUL_CONTENT: "Remove harmful, violent, or dangerous content from your prompt",
            GuardrailType.PRIVACY_VIOLATION: "Remove requests for personal or confidential information",
            GuardrailType.ETHICAL_VIOLATION: "Ensure your prompt follows ethical AI usage guidelines",
            GuardrailType.BIAS_DETECTION: "Rephrase to avoid stereotypes and biased language",
            GuardrailType.INAPPROPRIATE_REQUEST: "Remove inappropriate or adult content from your request",
            GuardrailType.SAFETY_CONSTRAINT: "Modify prompt to comply with AI safety constraints",
            GuardrailType.OUTPUT_VALIDATION: "Review and modify the generated content"
        }
        return recommendations.get(rule.rule_type, "Review and modify your prompt")

    def _get_recommendations(self, violations: List[GuardrailViolationResult]) -> List[str]:
        """Get overall recommendations based on violations."""
        if not violations:
            return ["Prompt passed all guardrail checks"]

        recommendations = []
        violation_types = set(v.rule_type for v in violations)

        for violation_type in violation_types:
            if violation_type == GuardrailType.HARMFUL_CONTENT:
                recommendations.append("Remove any harmful, violent, or dangerous content")
            elif violation_type == GuardrailType.PRIVACY_VIOLATION:
                recommendations.append("Avoid requesting personal or confidential information")
            elif violation_type == GuardrailType.ETHICAL_VIOLATION:
                recommendations.append("Ensure ethical AI usage and avoid deceptive requests")
            elif violation_type == GuardrailType.BIAS_DETECTION:
                recommendations.append("Use inclusive language and avoid stereotypes")
            elif violation_type == GuardrailType.INAPPROPRIATE_REQUEST:
                recommendations.append("Keep content appropriate and professional")
            elif violation_type == GuardrailType.SAFETY_CONSTRAINT:
                recommendations.append("Respect AI safety guidelines and limitations")

        return recommendations

    def _violation_to_dict(self, violation: GuardrailViolationResult) -> Dict[str, Any]:
        """Convert violation result to dictionary."""
        return {
            "rule_name": violation.rule_name,
            "rule_type": violation.rule_type.value,
            "severity": violation.severity.value,
            "description": violation.description,
            "matched_text": violation.matched_text,
            "position": violation.position,
            "confidence": violation.confidence,
            "recommendation": violation.recommendation
        }

    def get_guardrail_stats(self) -> Dict[str, Any]:
        """Get statistics about guardrail rules."""
        enabled_rules = [r for r in self.rules if r.enabled]
        disabled_rules = [r for r in self.rules if not r.enabled]

        rule_types = {}
        for rule in enabled_rules:
            rule_type = rule.rule_type.value
            if rule_type not in rule_types:
                rule_types[rule_type] = 0
            rule_types[rule_type] += 1

        return {
            "total_rules": len(self.rules),
            "enabled_rules": len(enabled_rules),
            "disabled_rules": len(disabled_rules),
            "rule_types": rule_types,
            "engine_enabled": self.enabled
        }

    def export_rules(self) -> List[Dict[str, Any]]:
        """Export guardrail rules configuration."""
        return [
            {
                "name": rule.name,
                "description": rule.description,
                "rule_type": rule.rule_type.value,
                "severity": rule.severity.value,
                "patterns": rule.patterns,
                "keywords": rule.keywords,
                "enabled": rule.enabled
            }
            for rule in self.rules
        ]


# Global guardrail engine instance
guardrail_engine = GuardrailEngine()
