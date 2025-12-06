"""
This package provides a centralized function for creating LLM instances.
"""

from .provider import create_llm

__all__ = [
    "create_llm",
]
