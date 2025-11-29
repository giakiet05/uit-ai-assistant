"""
This module provides a simple and flexible way to create LlamaIndex LLM instances.
"""

import os
from dotenv import load_dotenv
from llama_index.core.llms import LLM
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI
from llama_index.llms.gemini import Gemini

from src.config import settings

# Load environment variables from .env file
load_dotenv()

def _create_ollama_llm(model: str, **kwargs) -> Ollama:
    """
    Creates a LlamaIndex Ollama instance with a robust try-except block.
    """
    default_kwargs = {
        "base_url": "http://localhost:11434",
        "temperature": 0.1,
        "request_timeout": 120.0,
        "system_prompt": "Bạn là một trợ lý AI chuyên gia về lĩnh vực giáo dục đại học. Câu trả lời của bạn phải dựa trên ngữ cảnh được cung cấp. Luôn luôn trả lời bằng tiếng Việt."
    }
    final_kwargs = {**default_kwargs, **kwargs}

    print(f"[INFO] Attempting to create Ollama LLM with model: {model}")
    try:
        llm = Ollama(model=model, **final_kwargs)
        print("✅ Ollama LLM instance created.")
        return llm
    except Exception as e:
        print(f"[ERROR] Failed to create Ollama LLM instance.")
        print(f"  Error details: {e}")
        print("  Suggestions:")
        print("    1. Ensure the Ollama server is running: 'ollama serve'")
        print(f"    2. Ensure the model '{model}' is available: 'ollama list' or 'ollama pull {model}'")
        raise ConnectionError("Failed to initialize Ollama LLM. Please check the server and model availability.")

def _create_openai_llm(model: str, **kwargs) -> OpenAI:
    """
    Creates a LlamaIndex OpenAI instance.
    """
    api_key = settings.credentials.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables. Please create a .env file.")

    default_kwargs = {
        "temperature": 0.5,  # Balanced for RAG: factual yet natural
        "system_prompt": "Bạn là một trợ lý AI chuyên gia về lĩnh vực giáo dục đại học. Câu trả lời của bạn phải dựa trên ngữ cảnh được cung cấp. Luôn luôn trả lời bằng tiếng Việt và đầy đủ, chi tiết.",
    }
    final_kwargs = {**default_kwargs, **kwargs}

    print(f"[INFO] Creating OpenAI LLM with model: {model}")
    return OpenAI(model=model, api_key=api_key, **final_kwargs)

def _create_gemini_llm(model: str, **kwargs) -> Gemini:
    """
    Creates a LlamaIndex Gemini instance.
    """
    api_key = settings.credentials.GOOGLE_API_KEY
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables. Please create a .env file.")

    default_kwargs = {
        "temperature": 0.5,  # Balanced for text generation
    }
    final_kwargs = {**default_kwargs, **kwargs}

    print(f"[INFO] Creating Gemini LLM with model: {model}")
    return Gemini(model=model, api_key=api_key, **final_kwargs)

def create_llm(provider: str, model: str, **kwargs) -> LLM:
    """
    A factory function that creates and returns a LlamaIndex LLM instance.
    """
    provider = provider.lower()

    if provider == "ollama":
        return _create_ollama_llm(model=model, **kwargs)
    elif provider == "openai":
        return _create_openai_llm(model=model, **kwargs)
    elif provider == "gemini":
        return _create_gemini_llm(model=model, **kwargs)
    else:
        raise ValueError(f"Unsupported LLM provider: '{provider}'. Supported: ['ollama', 'openai', 'gemini']")
