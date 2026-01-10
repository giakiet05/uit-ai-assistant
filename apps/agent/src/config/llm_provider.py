"""
This module provides a simple and flexible way to create LangChain LLM instances.
"""

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from .settings import settings
from ..utils.logger import logger

# Load environment variables from .env file
load_dotenv()


def _create_openai_llm(model: str, **kwargs) -> ChatOpenAI:
    """
    Creates a LangChain ChatOpenAI instance.

    Args:
        model: Model name (e.g., "gpt-4o", "gpt-5-mini")
        **kwargs: Additional parameters

    Returns:
        ChatOpenAI instance
    """
    api_key = settings.credentials.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables. Please create a .env file.")

    logger.info(f"[LLM] Creating OpenAI LLM with model: {model}")
    return ChatOpenAI(model=model, api_key=api_key, **kwargs)


def _create_gemini_llm(model: str, **kwargs) -> ChatGoogleGenerativeAI:
    """
    Creates a LangChain ChatGoogleGenerativeAI instance.

    Args:
        model: Model name (e.g., "gemini-2.0-flash-exp", "gemini-1.5-pro")
        **kwargs: Additional parameters

    Returns:
        ChatGoogleGenerativeAI instance
    """
    api_key = settings.credentials.GOOGLE_API_KEY
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables. Please create a .env file.")

    logger.info(f"[LLM] Creating Gemini LLM with model: {model}")
    return ChatGoogleGenerativeAI(model=model, google_api_key=api_key, **kwargs)


def create_llm(provider: str, model: str, **kwargs):
    """
    A factory function that creates and returns a LangChain LLM instance.

    Args:
        provider: LLM provider ("openai" or "gemini")
        model: Model name/identifier
        **kwargs: Additional provider-specific parameters

    Returns:
        LLM instance configured with the specified provider and model

    Examples:
        # Basic usage
        llm = create_llm("openai", "gpt-5-mini")

        # With custom parameters
        llm = create_llm("openai", "gpt-4o", max_tokens=1000)

        # Gemini model
        llm = create_llm("gemini", "gemini-2.0-flash-exp")
    """
    provider = provider.lower()

    if provider == "openai":
        return _create_openai_llm(model=model, **kwargs)
    elif provider == "gemini":
        return _create_gemini_llm(model=model, **kwargs)
    else:
        raise ValueError(f"Unsupported LLM provider: '{provider}'. Supported: ['openai', 'gemini']")
