"""
Enhanced configuration module for Think-Tank.

This module provides a robust configuration system with:
- Environment variable loading with validation
- Type checking and conversion
- Default fallback values
- Secret management integration
- Configuration validation
"""

import os
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from pydantic import BaseSettings, validator, Field, PostgresDsn, RedisDsn, HttpUrl
from pydantic_settings import BaseSettings
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("config")

class Settings(BaseSettings):
    """
    Application settings with validation and fallbacks.
    
    This class handles loading configuration from environment variables,
    with proper validation, type conversion, and fallback values.
    """
    # Project metadata
    PROJECT_NAME: str = "Think-Tank-IO"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Hybrid task management and AI research platform"
    
    # API configuration
    API_V1_STR: str = "/api"
    API_PREFIX: str = "/api/v1"
    
    # Environment
    DEBUG: bool = Field(False, description="Enable debug mode")
    ENVIRONMENT: str = Field("development", description="deployment environment (development, staging, production)")
    
    # Database settings with validation
    DATABASE_URL: PostgresDsn = Field(
        "postgresql://thinktank:thinktank123@localhost:5432/thinktank",
        description="PostgreSQL connection string"
    )
    
    # Redis settings with validation
    REDIS_URL: RedisDsn = Field(
        "redis://localhost:6379/0",
        description="Redis connection string"
    )
    
    # Vector DB settings
    VECTOR_DB_URL: HttpUrl = Field(
        "http://localhost:8000",
        description="ChromaDB connection URL"
    )
    VECTOR_DB_PERSIST_DIRECTORY: str = Field(
        "./vector_db",
        description="Directory to persist vector database"
    )
    
    # CORS settings with validation
    BACKEND_CORS_ORIGINS: List[str] = Field(
        ["http://localhost:3000", "http://localhost:8000"],
        description="List of allowed CORS origins"
    )
    
    # Security settings
    SECRET_KEY: str = Field(
        ...,  # Required field
        description="Secret key for JWT token generation and validation"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        11520,  # 8 days
        description="Minutes before access token expires",
        ge=1,  # Greater than or equal to 1
    )
    
    # AI service settings
    OPENAI_API_KEY: Optional[str] = Field(
        None,
        description="OpenAI API key for language model access"
    )
    OPENAI_MODEL: str = Field(
        "gpt-4",
        description="OpenAI model to use"
    )
    OPENAI_EMBEDDING_MODEL: str = Field(
        "text-embedding-ada-002",
        description="OpenAI embedding model to use"
    )
    ANTHROPIC_API_KEY: Optional[str] = Field(
        None,
        description="Anthropic API key for Claude model access"
    )
    ANTHROPIC_MODEL: str = Field(
        "claude-3-opus-20240229",
        description="Anthropic model to use"
    )
    
    # Caching settings
    CACHE_TTL: int = Field(
        3600,
        description="Default cache TTL in seconds",
        ge=1
    )
    CACHE_ENABLED: bool = Field(
        True,
        description="Enable caching"
    )
    CACHE_STRATEGY: str = Field(
        "multi_level",
        description="Caching strategy (single, multi_level)"
    )
    
    # Resource limits
    MAX_CONCURRENT_REQUESTS: int = Field(
        10,
        description="Maximum number of concurrent requests",
        ge=1
    )
    REQUEST_TIMEOUT_SECONDS: int = Field(
        30,
        description="Request timeout in seconds",
        ge=1
    )
    RATE_LIMIT_REQUESTS: int = Field(
        100,
        description="Number of requests allowed per period",
        ge=1
    )
    RATE_LIMIT_PERIOD_SECONDS: int = Field(
        60,
        description="Rate limit period in seconds",
        ge=1
    )
    
    # Monitoring
    ENABLE_TELEMETRY: bool = Field(
        False,
        description="Enable telemetry data collection"
    )
    LOG_LEVEL: str = Field(
        "info",
        description="Logging level"
    )
    
    # Feature flags
    ENABLE_ADVANCED_ANALYTICS: bool = Field(
        False,
        description="Enable advanced analytics features"
    )
    ENABLE_USER_FEEDBACK: bool = Field(
        True,
        description="Enable user feedback collection"
    )
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = {"development", "staging", "production"}
        if v.lower() not in allowed:
            logger.warning(
                f"Environment {v} not in {allowed}, defaulting to development"
            )
            return "development"
        return v.lower()
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = {"debug", "info", "warning", "error", "critical"}
        if v.lower() not in allowed:
            logger.warning(
                f"Log level {v} not in {allowed}, defaulting to info"
            )
            return "info"
        return v.lower()
    
    @validator("CACHE_STRATEGY")
    def validate_cache_strategy(cls, v: str) -> str:
        """Validate cache strategy."""
        allowed = {"single", "multi_level"}
        if v.lower() not in allowed:
            logger.warning(
                f"Cache strategy {v} not in {allowed}, defaulting to multi_level"
            )
            return "multi_level"
        return v.lower()
    
    def configure_logging(self) -> None:
        """Configure logging based on settings."""
        log_level = getattr(logging, self.LOG_LEVEL.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        logger.setLevel(log_level)
        logger.info(f"Logging configured with level: {self.LOG_LEVEL}")
    
    def get_db_connection_args(self) -> Dict[str, Any]:
        """Get database connection arguments."""
        return {
            "url": self.DATABASE_URL,
            "connect_args": {"connect_timeout": 10},
            "pool_size": 5,
            "max_overflow": 10,
        }
    
    def get_redis_connection_args(self) -> Dict[str, Any]:
        """Get Redis connection arguments."""
        return {
            "url": self.REDIS_URL,
            "socket_timeout": 5,
            "socket_connect_timeout": 5,
        }
    
    def validate(self) -> None:
        """Validate the entire configuration."""
        # Check for required API keys based on environment
        if self.ENVIRONMENT == "production":
            if not self.OPENAI_API_KEY and not self.ANTHROPIC_API_KEY:
                logger.error("No AI service API keys provided in production environment")
                raise ValueError("At least one AI service API key is required in production")
            
            if self.SECRET_KEY == "replace_with_strong_secret_key_in_production":
                logger.error("Default secret key used in production environment")
                raise ValueError("Default secret key cannot be used in production")
        
        # Log warnings for development environment
        if self.ENVIRONMENT == "development":
            if self.DEBUG:
                logger.warning("Debug mode is enabled in development environment")
            
            if not self.OPENAI_API_KEY and not self.ANTHROPIC_API_KEY:
                logger.warning("No AI service API keys provided, some features may not work")
        
        logger.info(f"Configuration validated for {self.ENVIRONMENT} environment")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Application settings
    """
    settings = Settings()
    settings.configure_logging()
    try:
        settings.validate()
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        if settings.ENVIRONMENT == "production":
            raise
    return settings


# Create a global settings instance
settings = get_settings()
