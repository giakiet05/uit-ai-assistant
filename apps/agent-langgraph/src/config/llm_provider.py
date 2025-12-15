"""
This module provides a simple and flexible way to create LangChain LLM instances.
"""

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from .settings import settings

# Load environment variables from .env file
load_dotenv()


def _create_openai_llm(model: str, **kwargs) -> ChatOpenAI:
    """
    Creates a LangChain ChatOpenAI instance.

    Args:
        model: Model name (e.g., "gpt-4o", "gpt-4o-mini")
        **kwargs: Additional parameters (temperature, etc.)

    Returns:
        ChatOpenAI instance
    """
    api_key = settings.credentials.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables. Please create a .env file.")

    default_kwargs = {
        "temperature": 0.5,  # Default temperature, can be overridden
    }
    final_kwargs = {**default_kwargs, **kwargs}

    print(f"[LLM] Creating OpenAI LLM with model: {model}")
    return ChatOpenAI(model=model, api_key=api_key, **final_kwargs)


def _create_gemini_llm(model: str, **kwargs) -> ChatGoogleGenerativeAI:
    """
    Creates a LangChain ChatGoogleGenerativeAI instance.

    Args:
        model: Model name (e.g., "gemini-2.0-flash-exp", "gemini-1.5-pro")
        **kwargs: Additional parameters (temperature, etc.)

    Returns:
        ChatGoogleGenerativeAI instance
    """
    api_key = settings.credentials.GOOGLE_API_KEY
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables. Please create a .env file.")

    default_kwargs = {
        "temperature": 0.5,  # Default temperature, can be overridden
    }
    final_kwargs = {**default_kwargs, **kwargs}

    print(f"[LLM] Creating Gemini LLM with model: {model}")
    return ChatGoogleGenerativeAI(model=model, google_api_key=api_key, **final_kwargs)


def create_llm(provider: str, model: str, **kwargs):
    """
    A factory function that creates and returns a LangChain LLM instance.

    Args:
        provider: LLM provider ("openai" or "gemini")
        model: Model name/identifier
        **kwargs: Additional parameters to override defaults
            - temperature (float): Controls randomness (default: 0.5)
            - Other provider-specific parameters

    Returns:
        LLM instance configured with the specified provider and model

    Examples:
        # Use default temperature (0.5)
        llm = create_llm("openai", "gpt-4o")

        # Override temperature
        llm = create_llm("openai", "gpt-4o", temperature=0.7)

        # Gemini model
        llm = create_llm("gemini", "gemini-2.0-flash-exp", temperature=0.3)
    """
    provider = provider.lower()

    if provider == "openai":
        return _create_openai_llm(model=model, **kwargs)
    elif provider == "gemini":
        return _create_gemini_llm(model=model, **kwargs)
    else:
        raise ValueError(f"Unsupported LLM provider: '{provider}'. Supported: ['openai', 'gemini']")
