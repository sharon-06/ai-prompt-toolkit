"""
Core configuration management for AI Prompt Toolkit.
Supports flag-based configuration for multiple LLM providers.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseSettings, Field, validator
from pydantic_settings import BaseSettings as PydanticBaseSettings


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    BEDROCK = "bedrock"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseConfig(PydanticBaseSettings):
    """Database configuration."""
    url: str = Field(default="sqlite:///./ai_prompt_toolkit.db", env="DATABASE_URL")
    echo: bool = Field(default=False, env="DATABASE_ECHO")
    pool_size: int = Field(default=5, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")


class RedisConfig(PydanticBaseSettings):
    """Redis configuration for caching and task queue."""
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    db: int = Field(default=0, env="REDIS_DB")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    url: Optional[str] = Field(default=None, env="REDIS_URL")


class OllamaConfig(PydanticBaseSettings):
    """Ollama configuration."""
    enabled: bool = Field(default=True, env="OLLAMA_ENABLED")
    base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    model: str = Field(default="llama3.1:latest", env="OLLAMA_MODEL")
    temperature: float = Field(default=0.7, env="OLLAMA_TEMPERATURE")
    max_tokens: int = Field(default=2048, env="OLLAMA_MAX_TOKENS")
    timeout: int = Field(default=60, env="OLLAMA_TIMEOUT")


class OpenAIConfig(PydanticBaseSettings):
    """OpenAI configuration."""
    enabled: bool = Field(default=False, env="OPENAI_ENABLED")
    api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    max_tokens: int = Field(default=2048, env="OPENAI_MAX_TOKENS")
    organization: Optional[str] = Field(default=None, env="OPENAI_ORGANIZATION")


class BedrockConfig(PydanticBaseSettings):
    """AWS Bedrock configuration."""
    enabled: bool = Field(default=False, env="BEDROCK_ENABLED")
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    model: str = Field(default="anthropic.claude-v2", env="BEDROCK_MODEL")
    temperature: float = Field(default=0.7, env="BEDROCK_TEMPERATURE")
    max_tokens: int = Field(default=2048, env="BEDROCK_MAX_TOKENS")


class AnthropicConfig(PydanticBaseSettings):
    """Anthropic configuration."""
    enabled: bool = Field(default=False, env="ANTHROPIC_ENABLED")
    api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    model: str = Field(default="claude-3-sonnet-20240229", env="ANTHROPIC_MODEL")
    temperature: float = Field(default=0.7, env="ANTHROPIC_TEMPERATURE")
    max_tokens: int = Field(default=2048, env="ANTHROPIC_MAX_TOKENS")


class SecurityConfig(PydanticBaseSettings):
    """Security configuration."""
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    enable_prompt_injection_detection: bool = Field(default=True, env="ENABLE_PROMPT_INJECTION_DETECTION")
    max_prompt_length: int = Field(default=10000, env="MAX_PROMPT_LENGTH")


class OptimizationConfig(PydanticBaseSettings):
    """Prompt optimization configuration."""
    enabled: bool = Field(default=True, env="OPTIMIZATION_ENABLED")
    max_iterations: int = Field(default=5, env="OPTIMIZATION_MAX_ITERATIONS")
    target_cost_reduction: float = Field(default=0.2, env="OPTIMIZATION_TARGET_COST_REDUCTION")
    performance_threshold: float = Field(default=0.8, env="OPTIMIZATION_PERFORMANCE_THRESHOLD")
    use_genetic_algorithm: bool = Field(default=True, env="OPTIMIZATION_USE_GENETIC_ALGORITHM")
    population_size: int = Field(default=10, env="OPTIMIZATION_POPULATION_SIZE")


class Settings(PydanticBaseSettings):
    """Main application settings."""
    
    # Application
    app_name: str = Field(default="AI Prompt Toolkit", env="APP_NAME")
    version: str = Field(default="0.1.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: LogLevel = Field(default=LogLevel.INFO, env="LOG_LEVEL")
    
    # API
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    reload: bool = Field(default=False, env="RELOAD")
    
    # Default LLM Provider
    default_llm_provider: LLMProvider = Field(default=LLMProvider.OLLAMA, env="DEFAULT_LLM_PROVIDER")
    
    # Sub-configurations
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    ollama: OllamaConfig = OllamaConfig()
    openai: OpenAIConfig = OpenAIConfig()
    bedrock: BedrockConfig = BedrockConfig()
    anthropic: AnthropicConfig = AnthropicConfig()
    security: SecurityConfig = SecurityConfig()
    optimization: OptimizationConfig = OptimizationConfig()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("default_llm_provider")
    def validate_default_provider(cls, v, values):
        """Ensure the default provider is enabled."""
        if v == LLMProvider.OLLAMA and not values.get("ollama", {}).get("enabled", True):
            raise ValueError("Default LLM provider (Ollama) is not enabled")
        return v
    
    def get_enabled_providers(self) -> List[LLMProvider]:
        """Get list of enabled LLM providers."""
        enabled = []
        if self.ollama.enabled:
            enabled.append(LLMProvider.OLLAMA)
        if self.openai.enabled and self.openai.api_key:
            enabled.append(LLMProvider.OPENAI)
        if self.bedrock.enabled:
            enabled.append(LLMProvider.BEDROCK)
        if self.anthropic.enabled and self.anthropic.api_key:
            enabled.append(LLMProvider.ANTHROPIC)
        return enabled
    
    def get_provider_config(self, provider: LLMProvider) -> Dict[str, Any]:
        """Get configuration for a specific provider."""
        config_map = {
            LLMProvider.OLLAMA: self.ollama.dict(),
            LLMProvider.OPENAI: self.openai.dict(),
            LLMProvider.BEDROCK: self.bedrock.dict(),
            LLMProvider.ANTHROPIC: self.anthropic.dict(),
        }
        return config_map.get(provider, {})


# Global settings instance
settings = Settings()
