"""
LLM Factory for creating and managing different LLM providers.
"""

from typing import Dict, Optional, Any
import structlog
from langchain.llms.base import LLM
from langchain_community.llms import Ollama
from langchain_openai import OpenAI
from langchain_aws import BedrockLLM
from langchain_community.llms import Anthropic

from ai_prompt_toolkit.core.config import settings, LLMProvider
from ai_prompt_toolkit.core.exceptions import LLMProviderError, ConfigurationError


class LLMFactory:
    """Factory for creating and managing LLM instances."""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self._llm_instances: Dict[LLMProvider, LLM] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all enabled LLM providers."""
        if self._initialized:
            return
        
        enabled_providers = settings.get_enabled_providers()
        self.logger.info("Initializing LLM providers", providers=enabled_providers)
        
        for provider in enabled_providers:
            try:
                llm = await self._create_llm(provider)
                self._llm_instances[provider] = llm
                self.logger.info("LLM provider initialized", provider=provider.value)
            except Exception as e:
                self.logger.error(
                    "Failed to initialize LLM provider",
                    provider=provider.value,
                    error=str(e)
                )
                if provider == settings.default_llm_provider:
                    raise ConfigurationError(
                        f"Failed to initialize default LLM provider {provider.value}: {str(e)}"
                    )
        
        if not self._llm_instances:
            raise ConfigurationError("No LLM providers could be initialized")
        
        self._initialized = True
    
    async def _create_llm(self, provider: LLMProvider) -> LLM:
        """Create an LLM instance for the specified provider."""
        config = settings.get_provider_config(provider)
        
        if provider == LLMProvider.OLLAMA:
            return self._create_ollama_llm(config)
        elif provider == LLMProvider.OPENAI:
            return self._create_openai_llm(config)
        elif provider == LLMProvider.BEDROCK:
            return self._create_bedrock_llm(config)
        elif provider == LLMProvider.ANTHROPIC:
            return self._create_anthropic_llm(config)
        else:
            raise LLMProviderError(f"Unsupported provider: {provider.value}", provider.value)
    
    def _create_ollama_llm(self, config: Dict[str, Any]) -> Ollama:
        """Create Ollama LLM instance."""
        try:
            return Ollama(
                base_url=config["base_url"],
                model=config["model"],
                temperature=config["temperature"],
                num_predict=config["max_tokens"],
                timeout=config["timeout"],
            )
        except Exception as e:
            raise LLMProviderError(f"Failed to create Ollama LLM: {str(e)}", "ollama")
    
    def _create_openai_llm(self, config: Dict[str, Any]) -> OpenAI:
        """Create OpenAI LLM instance."""
        if not config.get("api_key"):
            raise LLMProviderError("OpenAI API key is required", "openai")
        
        try:
            return OpenAI(
                api_key=config["api_key"],
                model=config["model"],
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
                organization=config.get("organization"),
            )
        except Exception as e:
            raise LLMProviderError(f"Failed to create OpenAI LLM: {str(e)}", "openai")
    
    def _create_bedrock_llm(self, config: Dict[str, Any]) -> BedrockLLM:
        """Create AWS Bedrock LLM instance."""
        try:
            credentials_kwargs = {}
            if config.get("aws_access_key_id"):
                credentials_kwargs.update({
                    "aws_access_key_id": config["aws_access_key_id"],
                    "aws_secret_access_key": config["aws_secret_access_key"],
                })
            
            return BedrockLLM(
                model_id=config["model"],
                region_name=config["aws_region"],
                model_kwargs={
                    "temperature": config["temperature"],
                    "max_tokens_to_sample": config["max_tokens"],
                },
                **credentials_kwargs
            )
        except Exception as e:
            raise LLMProviderError(f"Failed to create Bedrock LLM: {str(e)}", "bedrock")
    
    def _create_anthropic_llm(self, config: Dict[str, Any]) -> Anthropic:
        """Create Anthropic LLM instance."""
        if not config.get("api_key"):
            raise LLMProviderError("Anthropic API key is required", "anthropic")
        
        try:
            return Anthropic(
                api_key=config["api_key"],
                model=config["model"],
                temperature=config["temperature"],
                max_tokens_to_sample=config["max_tokens"],
            )
        except Exception as e:
            raise LLMProviderError(f"Failed to create Anthropic LLM: {str(e)}", "anthropic")
    
    def get_llm(self, provider: Optional[LLMProvider] = None) -> LLM:
        """Get LLM instance for the specified provider."""
        if not self._initialized:
            raise ConfigurationError("LLM factory not initialized")
        
        if provider is None:
            provider = settings.default_llm_provider
        
        if provider not in self._llm_instances:
            raise LLMProviderError(f"Provider {provider.value} not available", provider.value)
        
        return self._llm_instances[provider]
    
    def get_available_providers(self) -> list[LLMProvider]:
        """Get list of available (initialized) providers."""
        return list(self._llm_instances.keys())
    
    def is_provider_available(self, provider: LLMProvider) -> bool:
        """Check if a provider is available."""
        return provider in self._llm_instances


# Global LLM factory instance
llm_factory = LLMFactory()
