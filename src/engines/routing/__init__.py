"""
Query routing module for multi-collection RAG system.

Provides strategies for routing user queries to appropriate ChromaDB collections:
- QueryAllRouter: Query all collections (simple, robust)
- LLMClassificationRouter: LLM-based classification (efficient, semantic)

Usage:
    >>> from src.engines.routing import create_router
    >>>
    >>> # Create router from settings
    >>> router = create_router()
    >>>
    >>> # Route a query
    >>> decision = router.route("UIT có bao nhiêu loại học phần?")
    >>> print(decision.collections)
    ["regulation"]
"""

from .base_router import BaseQueryRouter, RoutingDecision
from .query_all_router import QueryAllRouter
from .llm_classification_router import LLMClassificationRouter
from .router_factory import create_router, get_available_strategies

__all__ = [
    # Base classes
    "BaseQueryRouter",
    "RoutingDecision",

    # Concrete routers
    "QueryAllRouter",
    "LLMClassificationRouter",

    # Factory
    "create_router",
    "get_available_strategies",
]
