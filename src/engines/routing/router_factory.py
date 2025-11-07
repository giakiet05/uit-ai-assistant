"""
Router Factory - Creates routers based on configuration.

Provides a factory function to instantiate the appropriate router
based on the routing strategy specified in settings.
"""

from typing import List, Optional

from src.config.settings import settings
from .base_router import BaseQueryRouter
from .query_all_router import QueryAllRouter
from .llm_classification_router import LLMClassificationRouter


def create_router(
    strategy: Optional[str] = None,
    available_collections: Optional[List[str]] = None
) -> BaseQueryRouter:
    """
    Create a router instance based on strategy.

    Args:
        strategy: Routing strategy name (None = use settings)
                 Options: "query_all", "llm_classification"
        available_collections: List of collection names (None = use settings)

    Returns:
        Configured router instance

    Raises:
        ValueError: If strategy is invalid

    Example:
        >>> from src.engines.routing.router_factory import create_router
        >>>
        >>> # Use settings (default)
        >>> router = create_router()
        >>>
        >>> # Override strategy
        >>> router = create_router(strategy="query_all")
        >>>
        >>> # Override collections
        >>> router = create_router(
        ...     strategy="llm_classification",
        ...     available_collections=["regulations"]
        ... )
    """
    # Use defaults from settings if not provided
    if strategy is None:
        strategy = settings.query_routing.STRATEGY

    if available_collections is None:
        available_collections = settings.query_routing.AVAILABLE_COLLECTIONS

    # Validate strategy
    strategy = strategy.lower().strip()

    # Create router based on strategy
    if strategy == "query_all":
        return QueryAllRouter(available_collections)

    elif strategy == "llm_classification":
        return LLMClassificationRouter(available_collections)

    else:
        raise ValueError(
            f"Invalid routing strategy: '{strategy}'. "
            f"Valid options: 'query_all', 'llm_classification'"
        )


def get_available_strategies() -> List[str]:
    """
    Get list of available routing strategies.

    Returns:
        List of strategy names

    Example:
        >>> from src.engines.routing.router_factory import get_available_strategies
        >>> print(get_available_strategies())
        ["query_all", "llm_classification"]
    """
    return ["query_all", "llm_classification"]
