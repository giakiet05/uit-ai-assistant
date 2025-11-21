"""
Base router interface for query routing strategies.

Defines the abstract interface that all routing strategies must implement.
"""

from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass


@dataclass
class RoutingDecision:
    """
    Represents a routing decision for a user query.

    Attributes:
        collections: List of collection names to query
        strategy: Strategy name used for routing
        reasoning: Optional explanation of routing decision
    """
    collections: List[str]
    strategy: str
    reasoning: str = ""


class BaseQueryRouter(ABC):
    """
    Abstract base class for query routing strategies.

    All routing implementations must inherit from this class and
    implement the route() method.
    """

    def __init__(self, available_collections: List[str]):
        """
        Initialize router with available collections.

        Args:
            available_collections: List of collection names that can be queried
        """
        self.available_collections = available_collections

    @abstractmethod
    def route(self, query: str) -> RoutingDecision:
        """
        Route a user query to appropriate collections.

        Args:
            query: User query string

        Returns:
            RoutingDecision with collections to query and reasoning

        Example:
            >>> router = SomeRouter(["regulations", "curriculum"])
            >>> decision = router.route("UIT có bao nhiêu loại học phần?")
            >>> print(decision.collections)
            ["regulations"]
        """
        pass
