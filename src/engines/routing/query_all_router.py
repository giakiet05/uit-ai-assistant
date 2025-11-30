"""
Query All Router - Simple routing strategy that queries all collections.

This is the simplest and most robust routing strategy:
- Always queries all available collections
- Relies on vector similarity scores to rank results
- No risk of missing relevant documents due to misclassification

Use this strategy when:
- Collection count is small (2-3 collections)
- Query latency is acceptable
- Maximum recall is more important than speed
"""

from typing import List
from .base_router import BaseQueryRouter, RoutingDecision


class QueryAllRouter(BaseQueryRouter):
    """
    Routes all queries to all available collections.

    This strategy is simple and effective for small numbers of collections,
    as it ensures no relevant documents are missed due to routing errors.
    """

    def route(self, query: str) -> RoutingDecision:
        """
        Route query to all available collections.

        Args:
            query: User query string

        Returns:
            RoutingDecision with all collections

        Example:
            >>> router = QueryAllRouter(["regulation", "curriculum"])
            >>> decision = router.route("UIT có bao nhiêu loại học phần?")
            >>> print(decision.collections)
            ["regulation", "curriculum"]
            >>> print(decision.reasoning)
            "Query all collections strategy: searching all available collections"
        """
        return RoutingDecision(
            collections=self.available_collections,
            strategy="query_all",
            reasoning=f"Query all collections strategy: searching {len(self.available_collections)} collections"
        )
