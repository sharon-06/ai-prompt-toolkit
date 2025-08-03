"""
Prompt injection detection system.
"""

import re
import json
from typing import Dict, List, Any, Tuple
from enum import Enum
import structlog

from ai_prompt_toolkit.core.exceptions import PromptInjectionDetected


class InjectionType(str, Enum):
    """Types of prompt injection attacks."""
    INSTRUCTION_OVERRIDE = "instruction_override"
    CONTEXT_SWITCHING = "context_switching"
    ROLE_PLAYING = "role_playing"
    SYSTEM_PROMPT_LEAK = "system_prompt_leak"
    JAILBREAK = "jailbreak"
    DATA_EXTRACTION = "data_extraction"
    MALICIOUS_CODE = "malicious_code"


class ThreatLevel(str, Enum):
    """Threat levels for detected injections."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InjectionDetector:
    """Advanced prompt injection detection system."""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self._load_detection_rules()
    
    def _load_detection_rules(self):
        """Load detection rules and patterns."""
        
        # Instruction override patterns
        self.instruction_override_patterns = [
            r'ignore\s+(?:previous|all|the)\s+instructions?',
            r'forget\s+(?:everything|all|previous)',
            r'disregard\s+(?:previous|all|the)\s+instructions?',
            r'new\s+instructions?:',
            r'instead\s+of\s+(?:following|doing)',
            r'override\s+(?:previous|system)\s+instructions?',
            r'cancel\s+(?:previous|all)\s+instructions?'
        ]
        
        # Context switching patterns
        self.context_switching_patterns = [
            r'now\s+(?:you\s+are|act\s+as|pretend\s+to\s+be)',
            r'from\s+now\s+on\s+you\s+(?:are|will)',
            r'switch\s+to\s+(?:a\s+)?(?:new\s+)?(?:role|mode|character)',
            r'change\s+your\s+(?:role|behavior|personality)',
            r'you\s+are\s+no\s+longer',
            r'stop\s+being\s+(?:an?\s+)?(?:assistant|ai|bot)'
        ]
        
        # Role playing patterns
        self.role_playing_patterns = [
            r'pretend\s+(?:to\s+be|you\s+are)',
            r'act\s+(?:as|like)\s+(?:an?\s+)?(?:evil|malicious|harmful)',
            r'roleplay\s+as',
            r'imagine\s+you\s+are\s+(?:an?\s+)?(?:evil|malicious|harmful)',
            r'you\s+are\s+(?:an?\s+)?(?:evil|malicious|harmful|dangerous)',
            r'simulate\s+(?:being\s+)?(?:an?\s+)?(?:evil|malicious|harmful)'
        ]
        
        # System prompt leak patterns
        self.system_leak_patterns = [
            r'show\s+(?:me\s+)?(?:your\s+)?(?:system\s+)?(?:prompt|instructions)',
            r'what\s+(?:are\s+)?(?:your\s+)?(?:system\s+)?(?:prompt|instructions)',
            r'reveal\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions)',
            r'display\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions)',
            r'print\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions)',
            r'output\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions)'
        ]
        
        # Jailbreak patterns
        self.jailbreak_patterns = [
            r'jailbreak',
            r'dan\s+mode',
            r'developer\s+mode',
            r'unrestricted\s+mode',
            r'bypass\s+(?:safety|restrictions|guidelines)',
            r'remove\s+(?:safety|restrictions|limitations)',
            r'disable\s+(?:safety|restrictions|filters)',
            r'without\s+(?:restrictions|limitations|safety)'
        ]
        
        # Data extraction patterns
        self.data_extraction_patterns = [
            r'extract\s+(?:all\s+)?(?:data|information|content)',
            r'dump\s+(?:all\s+)?(?:data|database|memory)',
            r'show\s+(?:all\s+)?(?:data|files|content)',
            r'list\s+(?:all\s+)?(?:files|data|users)',
            r'access\s+(?:all\s+)?(?:data|files|database)',
            r'retrieve\s+(?:all\s+)?(?:data|information)'
        ]
        
        # Malicious code patterns
        self.malicious_code_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'eval\s*\(',
            r'exec\s*\(',
            r'system\s*\(',
            r'shell_exec\s*\(',
            r'passthru\s*\(',
            r'file_get_contents\s*\(',
            r'curl\s+.*(?:http|ftp)',
            r'wget\s+.*(?:http|ftp)'
        ]
        
        # Suspicious keywords
        self.suspicious_keywords = [
            'hack', 'exploit', 'vulnerability', 'backdoor', 'malware',
            'virus', 'trojan', 'phishing', 'scam', 'fraud',
            'illegal', 'criminal', 'terrorist', 'bomb', 'weapon',
            'drug', 'suicide', 'self-harm', 'violence', 'murder'
        ]
    
    def detect_injection(self, prompt: str) -> Dict[str, Any]:
        """Detect potential prompt injection attacks."""
        
        detections = []
        max_threat_level = ThreatLevel.LOW
        
        # Check each injection type
        detections.extend(self._check_instruction_override(prompt))
        detections.extend(self._check_context_switching(prompt))
        detections.extend(self._check_role_playing(prompt))
        detections.extend(self._check_system_leak(prompt))
        detections.extend(self._check_jailbreak(prompt))
        detections.extend(self._check_data_extraction(prompt))
        detections.extend(self._check_malicious_code(prompt))
        detections.extend(self._check_suspicious_keywords(prompt))
        
        # Determine overall threat level
        if detections:
            threat_levels = [d['threat_level'] for d in detections]
            if ThreatLevel.CRITICAL in threat_levels:
                max_threat_level = ThreatLevel.CRITICAL
            elif ThreatLevel.HIGH in threat_levels:
                max_threat_level = ThreatLevel.HIGH
            elif ThreatLevel.MEDIUM in threat_levels:
                max_threat_level = ThreatLevel.MEDIUM
        
        result = {
            "is_injection": len(detections) > 0,
            "threat_level": max_threat_level,
            "detections": detections,
            "risk_score": self._calculate_risk_score(detections),
            "recommendations": self._get_recommendations(detections)
        }
        
        # Log detection
        if detections:
            self.logger.warning(
                "Prompt injection detected",
                threat_level=max_threat_level.value,
                detection_count=len(detections),
                types=[d['type'] for d in detections]
            )
        
        return result
    
    def _check_instruction_override(self, prompt: str) -> List[Dict[str, Any]]:
        """Check for instruction override attempts."""
        detections = []
        
        for pattern in self.instruction_override_patterns:
            matches = re.finditer(pattern, prompt, re.IGNORECASE)
            for match in matches:
                detections.append({
                    "type": InjectionType.INSTRUCTION_OVERRIDE,
                    "threat_level": ThreatLevel.HIGH,
                    "pattern": pattern,
                    "match": match.group(),
                    "position": match.span(),
                    "description": "Attempt to override system instructions"
                })
        
        return detections
    
    def _check_context_switching(self, prompt: str) -> List[Dict[str, Any]]:
        """Check for context switching attempts."""
        detections = []
        
        for pattern in self.context_switching_patterns:
            matches = re.finditer(pattern, prompt, re.IGNORECASE)
            for match in matches:
                detections.append({
                    "type": InjectionType.CONTEXT_SWITCHING,
                    "threat_level": ThreatLevel.MEDIUM,
                    "pattern": pattern,
                    "match": match.group(),
                    "position": match.span(),
                    "description": "Attempt to switch AI context or role"
                })
        
        return detections
    
    def _check_role_playing(self, prompt: str) -> List[Dict[str, Any]]:
        """Check for malicious role playing attempts."""
        detections = []
        
        for pattern in self.role_playing_patterns:
            matches = re.finditer(pattern, prompt, re.IGNORECASE)
            for match in matches:
                detections.append({
                    "type": InjectionType.ROLE_PLAYING,
                    "threat_level": ThreatLevel.HIGH,
                    "pattern": pattern,
                    "match": match.group(),
                    "position": match.span(),
                    "description": "Attempt to make AI roleplay as malicious entity"
                })
        
        return detections
    
    def _check_system_leak(self, prompt: str) -> List[Dict[str, Any]]:
        """Check for system prompt leak attempts."""
        detections = []
        
        for pattern in self.system_leak_patterns:
            matches = re.finditer(pattern, prompt, re.IGNORECASE)
            for match in matches:
                detections.append({
                    "type": InjectionType.SYSTEM_PROMPT_LEAK,
                    "threat_level": ThreatLevel.MEDIUM,
                    "pattern": pattern,
                    "match": match.group(),
                    "position": match.span(),
                    "description": "Attempt to extract system prompt or instructions"
                })
        
        return detections
    
    def _check_jailbreak(self, prompt: str) -> List[Dict[str, Any]]:
        """Check for jailbreak attempts."""
        detections = []
        
        for pattern in self.jailbreak_patterns:
            matches = re.finditer(pattern, prompt, re.IGNORECASE)
            for match in matches:
                detections.append({
                    "type": InjectionType.JAILBREAK,
                    "threat_level": ThreatLevel.CRITICAL,
                    "pattern": pattern,
                    "match": match.group(),
                    "position": match.span(),
                    "description": "Attempt to bypass AI safety restrictions"
                })
        
        return detections
    
    def _check_data_extraction(self, prompt: str) -> List[Dict[str, Any]]:
        """Check for data extraction attempts."""
        detections = []
        
        for pattern in self.data_extraction_patterns:
            matches = re.finditer(pattern, prompt, re.IGNORECASE)
            for match in matches:
                detections.append({
                    "type": InjectionType.DATA_EXTRACTION,
                    "threat_level": ThreatLevel.HIGH,
                    "pattern": pattern,
                    "match": match.group(),
                    "position": match.span(),
                    "description": "Attempt to extract sensitive data"
                })
        
        return detections
    
    def _check_malicious_code(self, prompt: str) -> List[Dict[str, Any]]:
        """Check for malicious code injection."""
        detections = []
        
        for pattern in self.malicious_code_patterns:
            matches = re.finditer(pattern, prompt, re.IGNORECASE)
            for match in matches:
                detections.append({
                    "type": InjectionType.MALICIOUS_CODE,
                    "threat_level": ThreatLevel.CRITICAL,
                    "pattern": pattern,
                    "match": match.group(),
                    "position": match.span(),
                    "description": "Potential malicious code injection"
                })
        
        return detections
    
    def _check_suspicious_keywords(self, prompt: str) -> List[Dict[str, Any]]:
        """Check for suspicious keywords."""
        detections = []
        
        for keyword in self.suspicious_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', prompt, re.IGNORECASE):
                detections.append({
                    "type": InjectionType.JAILBREAK,
                    "threat_level": ThreatLevel.MEDIUM,
                    "pattern": keyword,
                    "match": keyword,
                    "position": None,
                    "description": f"Suspicious keyword detected: {keyword}"
                })
        
        return detections
    
    def _calculate_risk_score(self, detections: List[Dict[str, Any]]) -> float:
        """Calculate overall risk score (0-1)."""
        if not detections:
            return 0.0
        
        threat_weights = {
            ThreatLevel.LOW: 0.1,
            ThreatLevel.MEDIUM: 0.3,
            ThreatLevel.HIGH: 0.7,
            ThreatLevel.CRITICAL: 1.0
        }
        
        total_score = sum(threat_weights[d['threat_level']] for d in detections)
        max_possible_score = len(detections) * 1.0
        
        return min(1.0, total_score / max_possible_score)
    
    def _get_recommendations(self, detections: List[Dict[str, Any]]) -> List[str]:
        """Get security recommendations based on detections."""
        if not detections:
            return ["No security issues detected"]
        
        recommendations = [
            "Review and sanitize the input prompt",
            "Consider implementing additional input validation",
            "Monitor for similar patterns in future requests"
        ]
        
        threat_levels = [d['threat_level'] for d in detections]
        
        if ThreatLevel.CRITICAL in threat_levels:
            recommendations.extend([
                "CRITICAL: Block this request immediately",
                "Investigate the source of this request",
                "Consider implementing stricter security measures"
            ])
        elif ThreatLevel.HIGH in threat_levels:
            recommendations.extend([
                "HIGH RISK: Carefully review before processing",
                "Consider requiring additional authentication"
            ])
        
        return recommendations
    
    def validate_prompt(self, prompt: str, strict_mode: bool = False) -> bool:
        """Validate prompt and raise exception if injection detected."""
        detection_result = self.detect_injection(prompt)
        
        if detection_result["is_injection"]:
            if strict_mode or detection_result["threat_level"] in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                raise PromptInjectionDetected(
                    "Prompt injection attack detected",
                    details=detection_result
                )
        
        return True


# Global injection detector instance
injection_detector = InjectionDetector()
