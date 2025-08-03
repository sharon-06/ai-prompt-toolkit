"""
Tests for configuration management.
"""

import pytest
from ai_prompt_toolkit.core.config import Settings, LLMProvider


def test_default_settings():
    """Test default settings configuration."""
    settings = Settings()
    
    assert settings.app_name == "AI Prompt Toolkit"
    assert settings.version == "0.1.0"
    assert settings.default_llm_provider == LLMProvider.OLLAMA
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000


def test_ollama_config():
    """Test Ollama configuration."""
    settings = Settings()
    
    assert settings.ollama.enabled is True
    assert settings.ollama.base_url == "http://localhost:11434"
    assert settings.ollama.model == "llama3.1:latest"
    assert settings.ollama.temperature == 0.7


def test_enabled_providers():
    """Test getting enabled providers."""
    settings = Settings()
    
    enabled = settings.get_enabled_providers()
    assert LLMProvider.OLLAMA in enabled
    
    # OpenAI should not be enabled by default (no API key)
    assert LLMProvider.OPENAI not in enabled


def test_provider_config():
    """Test getting provider configuration."""
    settings = Settings()
    
    ollama_config = settings.get_provider_config(LLMProvider.OLLAMA)
    assert ollama_config["enabled"] is True
    assert ollama_config["model"] == "llama3.1:latest"
    
    openai_config = settings.get_provider_config(LLMProvider.OPENAI)
    assert openai_config["enabled"] is False


def test_security_config():
    """Test security configuration."""
    settings = Settings()
    
    assert settings.security.enable_prompt_injection_detection is True
    assert settings.security.max_prompt_length == 10000
    assert settings.security.algorithm == "HS256"


def test_optimization_config():
    """Test optimization configuration."""
    settings = Settings()
    
    assert settings.optimization.enabled is True
    assert settings.optimization.max_iterations == 5
    assert settings.optimization.target_cost_reduction == 0.2
    assert settings.optimization.use_genetic_algorithm is True
