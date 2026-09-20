"""Configurable LLM provider factory supporting Gemini, OpenAI, Anthropic, and Ollama."""
from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from app.config import settings


def get_llm(temperature: Optional[float] = None, model: Optional[str] = None) -> BaseChatModel:
    """Instantiate and return the configured LLM client based on environment variables."""
    provider = settings.LLM_PROVIDER.lower().strip()
    temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
    model_name = model or settings.LLM_MODEL

    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in your .env file."
            )
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temp,
        )

    elif provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not configured. Please set OPENAI_API_KEY in your .env file."
            )
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "langchain-openai is required for OpenAI provider. Run: uv add langchain-openai"
            )
        return ChatOpenAI(
            model=model_name,
            api_key=settings.OPENAI_API_KEY,
            temperature=temp,
        )

    elif provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is not configured. Please set ANTHROPIC_API_KEY in your .env file."
            )
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError(
                "langchain-anthropic is required for Anthropic provider. Run: uv add langchain-anthropic"
            )
        return ChatAnthropic(
            model=model_name,
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=temp,
        )

    elif provider == "ollama":
        try:
            from langchain_community.chat_models import ChatOllama
        except ImportError:
            raise ImportError(
                "langchain-community is required for Ollama provider. Run: uv add langchain-community"
            )
        return ChatOllama(
            model=model_name,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=temp,
        )

    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: '{provider}'. Supported options: 'gemini', 'openai', 'anthropic', 'ollama'."
        )
