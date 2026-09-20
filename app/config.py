"""Application configuration and environment settings."""
from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # LLM Settings
    LLM_PROVIDER: Literal["gemini", "openai", "anthropic", "ollama"] = "gemini"
    LLM_MODEL: str = "gemini-2.5-flash"
    LLM_TEMPERATURE: float = 0.2

    # Provider Keys
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Search Settings
    SEARCH_PROVIDER: Literal["tavily", "duckduckgo", "mock"] = "tavily"
    TAVILY_API_KEY: Optional[str] = Field(default=None)
    MAX_SEARCH_RESULTS: int = 5

    # Agent Loop Guardrails
    MAX_RETRY_LOOPS: int = 3
    MAX_PLAN_TASKS: int = 5

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True


# Global settings singleton
settings = Settings()
