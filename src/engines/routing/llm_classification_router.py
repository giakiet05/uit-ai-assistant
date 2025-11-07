"""
LLM Classification Router - Uses LLM to classify query intent and route accordingly.

This strategy uses a fast LLM (e.g., gpt-4o-mini) to classify the user's query
and route to the most relevant collection(s).

Advantages:
- Can handle semantic intent without keywords
- More efficient than query_all for large collection counts
- Adapts to natural language variations

Disadvantages:
- Adds LLM inference latency
- Risk of misclassification
- Requires API calls and costs

Use this strategy when:
- Collection count is large (5+ collections)
- Query latency is less critical
- Cost of querying all collections is high
"""

from typing import List
from llama_index.core.llms import ChatMessage
from llama_index.llms.openai import OpenAI

from src.config.settings import settings
from .base_router import BaseQueryRouter, RoutingDecision


class LLMClassificationRouter(BaseQueryRouter):
    """
    Routes queries using LLM-based classification.

    Uses a fast LLM to understand query intent and select relevant collections.
    """

    # Collection descriptions for classification prompt
    COLLECTION_DESCRIPTIONS = {
        "regulations": "Quy định, quy chế, quyết định, quy trình, hướng dẫn về chính sách và quản lý",
        "curriculum": "Chương trình đào tạo, danh mục môn học, nội dung học phần, kế hoạch đào tạo",
        "announcements": "Thông báo về lịch thi, lịch học, kết quả thi, sự kiện",
    }

    def __init__(self, available_collections: List[str]):
        """
        Initialize LLM classification router.

        Args:
            available_collections: List of collection names that can be queried
        """
        super().__init__(available_collections)

        # Initialize LLM (use fast, cheap model for classification)
        self.llm = OpenAI(
            model=settings.query_routing.CLASSIFICATION_MODEL,
            api_key=settings.credentials.OPENAI_API_KEY,
            temperature=settings.query_routing.CLASSIFICATION_TEMPERATURE
        )

    def route(self, query: str) -> RoutingDecision:
        """
        Route query using LLM classification.

        Args:
            query: User query string

        Returns:
            RoutingDecision with selected collections and reasoning

        Example:
            >>> router = LLMClassificationRouter(["regulations", "curriculum"])
            >>> decision = router.route("UIT có bao nhiêu loại học phần?")
            >>> print(decision.collections)
            ["regulations"]
            >>> print(decision.reasoning)
            "LLM classified query as 'regulations' based on policy/regulation intent"
        """
        # Build classification prompt
        prompt = self._build_classification_prompt(query)

        # Get LLM classification
        try:
            messages = [ChatMessage(role="user", content=prompt)]
            response = self.llm.chat(messages)
            classification = response.message.content.strip().lower()

            # Parse classification result
            selected_collections = self._parse_classification(classification)

            return RoutingDecision(
                collections=selected_collections,
                strategy="llm_classification",
                reasoning=f"LLM classified query as: {classification}"
            )

        except Exception as e:
            # Fallback to query_all on error
            print(f"[WARNING] LLM classification failed: {e}. Falling back to query_all.")
            return RoutingDecision(
                collections=self.available_collections,
                strategy="llm_classification_fallback",
                reasoning=f"LLM error, querying all collections. Error: {str(e)[:50]}"
            )

    def _build_classification_prompt(self, query: str) -> str:
        """
        Build classification prompt for LLM.

        Args:
            query: User query

        Returns:
            Formatted prompt string
        """
        # Build collection options text
        options_text = "\n".join([
            f"- {coll}: {self.COLLECTION_DESCRIPTIONS.get(coll, 'No description')}"
            for coll in self.available_collections
        ])

        prompt = f"""You are a query classification system for a university knowledge base.

Available collections:
{options_text}

User query: "{query}"

Task: Classify this query into ONE or MORE of the following categories: {', '.join(self.available_collections)}

Rules:
1. If the query is about policies, regulations, rules, or decisions, choose: regulations
2. If the query is about curriculum, courses, study programs, or academic content, choose: curriculum
3. If the query is about schedules, announcements, or events, choose: announcements
4. If the query could belong to multiple categories, list all relevant ones separated by commas
5. If unsure, return: all

Response format: Return ONLY the category name(s) or "all". No explanation.

Classification:"""

        return prompt

    def _parse_classification(self, classification: str) -> List[str]:
        """
        Parse LLM classification result into collection list.

        Args:
            classification: LLM response string

        Returns:
            List of collection names to query
        """
        classification = classification.lower().strip()

        # Handle "all" case
        if "all" in classification:
            return self.available_collections

        # Parse comma-separated collections
        selected = []
        for coll in self.available_collections:
            if coll in classification:
                selected.append(coll)

        # If no matches, default to all
        if not selected:
            print(f"[WARNING] Could not parse classification '{classification}', using all collections")
            return self.available_collections

        return selected
