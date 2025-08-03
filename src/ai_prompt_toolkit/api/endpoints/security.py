"""
Security and prompt injection detection API endpoints.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from ai_prompt_toolkit.security.injection_detector import injection_detector

router = APIRouter()


@router.post("/detect-injection")
async def detect_injection(request: Dict[str, str]):
    """Detect potential prompt injection attacks."""
    prompt = request.get("prompt", "")
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt text is required")
    
    detection_result = injection_detector.detect_injection(prompt)
    
    return {
        "prompt": prompt,
        "detection_result": detection_result
    }


@router.post("/validate-prompt")
async def validate_prompt(request: Dict[str, Any]):
    """Validate prompt and return safety assessment."""
    prompt = request.get("prompt", "")
    strict_mode = request.get("strict_mode", False)
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt text is required")
    
    try:
        is_valid = injection_detector.validate_prompt(prompt, strict_mode)
        detection_result = injection_detector.detect_injection(prompt)
        
        return {
            "prompt": prompt,
            "is_valid": is_valid,
            "is_safe": not detection_result["is_injection"],
            "detection_result": detection_result,
            "message": "Prompt is safe to use" if not detection_result["is_injection"] else "Potential security issues detected"
        }
    
    except Exception as e:
        return {
            "prompt": prompt,
            "is_valid": False,
            "is_safe": False,
            "error": str(e),
            "message": "Prompt validation failed"
        }


@router.get("/security-rules")
async def get_security_rules():
    """Get information about security rules and detection patterns."""
    return {
        "injection_types": [
            {
                "type": "instruction_override",
                "description": "Attempts to override system instructions",
                "examples": ["ignore previous instructions", "forget everything"]
            },
            {
                "type": "context_switching",
                "description": "Attempts to switch AI context or role",
                "examples": ["now you are", "act as", "pretend to be"]
            },
            {
                "type": "role_playing",
                "description": "Attempts to make AI roleplay as malicious entity",
                "examples": ["pretend you are evil", "act like a hacker"]
            },
            {
                "type": "system_prompt_leak",
                "description": "Attempts to extract system prompt",
                "examples": ["show your instructions", "what is your system prompt"]
            },
            {
                "type": "jailbreak",
                "description": "Attempts to bypass safety restrictions",
                "examples": ["jailbreak", "developer mode", "bypass safety"]
            },
            {
                "type": "data_extraction",
                "description": "Attempts to extract sensitive data",
                "examples": ["dump all data", "show all files"]
            },
            {
                "type": "malicious_code",
                "description": "Contains potentially malicious code",
                "examples": ["<script>", "eval()", "system()"]
            }
        ],
        "threat_levels": [
            {
                "level": "low",
                "description": "Minor security concern, monitor but allow"
            },
            {
                "level": "medium",
                "description": "Moderate risk, review before processing"
            },
            {
                "level": "high",
                "description": "High risk, careful review required"
            },
            {
                "level": "critical",
                "description": "Critical threat, block immediately"
            }
        ],
        "best_practices": [
            "Always validate user inputs before processing",
            "Use strict mode for sensitive applications",
            "Monitor and log security events",
            "Regularly update detection rules",
            "Implement rate limiting for API endpoints",
            "Use authentication for sensitive operations"
        ]
    }


@router.post("/security-scan")
async def security_scan(request: Dict[str, Any]):
    """Perform comprehensive security scan on prompt."""
    prompt = request.get("prompt", "")
    include_recommendations = request.get("include_recommendations", True)
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt text is required")
    
    # Perform injection detection
    detection_result = injection_detector.detect_injection(prompt)
    
    # Additional security checks
    security_metrics = {
        "prompt_length": len(prompt),
        "word_count": len(prompt.split()),
        "contains_urls": "http" in prompt.lower() or "www." in prompt.lower(),
        "contains_emails": "@" in prompt and "." in prompt,
        "contains_code": any(lang in prompt.lower() for lang in ["<script", "javascript", "python", "bash"]),
        "suspicious_patterns": len(detection_result["detections"]),
        "overall_risk_score": detection_result["risk_score"]
    }
    
    # Risk assessment
    risk_level = "low"
    if security_metrics["overall_risk_score"] > 0.7:
        risk_level = "critical"
    elif security_metrics["overall_risk_score"] > 0.5:
        risk_level = "high"
    elif security_metrics["overall_risk_score"] > 0.3:
        risk_level = "medium"
    
    result = {
        "prompt": prompt,
        "security_metrics": security_metrics,
        "detection_result": detection_result,
        "risk_assessment": {
            "risk_level": risk_level,
            "is_safe": detection_result["risk_score"] < 0.3,
            "confidence": 1.0 - detection_result["risk_score"]
        }
    }
    
    if include_recommendations:
        result["recommendations"] = detection_result["recommendations"]
    
    return result
