"""
HyDE (Hypothetical Document Embeddings) generator for QueryEngine.

HyDE improves retrieval by generating a hypothetical answer to the query,
then embedding the hypothetical answer instead of the query.

Hypothetical documents are typically closer to actual documents in vector space,
leading to better retrieval performance.
"""

from typing import Literal

from ..utils.logger import logger


class HyDEGenerator:
    """
    HyDE generator for query expansion.

    Generates hypothetical documents using LLM to improve retrieval quality.
    """

    def __init__(self, model: str = "gpt-5-nano", api_key: str = None):
        """
        Initialize HyDE generator.

        Args:
            model: LLM model name for generation
            api_key: OpenAI API key
        """
        self.model = model
        self.llm = None
        self._setup(api_key)

        logger.info(f"[HYDE] Using model: {self.model}")
        logger.info(f"[HYDE] HyDE LLM client initialized successfully")

    def _setup(self, api_key: str):
        """Setup OpenAI LLM client."""
        from openai import OpenAI

        self.llm = OpenAI(api_key=api_key)

    def generate(
        self,
        query: str,
        collection_type: Literal["regulation", "curriculum"]
    ) -> str:
        """
        Generate hypothetical document for query.

        Args:
            query: User's original query
            collection_type: Type of collection (regulation or curriculum)

        Returns:
            Hypothetical document text (100-200 words)
        """
        # Customize prompt based on collection type
        if collection_type == "regulation":
            context = "quy định, quy chế, văn bản hành chính của Đại học UIT"
        else:  # curriculum
            context = "chương trình đào tạo, môn học, học phần của các ngành tại UIT"

        prompt = f"""Bạn là chuyên gia về {context}.

Câu hỏi: {query}

Hãy viết một đoạn văn ngắn (100-200 từ) MÔ TẢ câu trả lời có thể có cho câu hỏi trên.
Không cần chính xác 100%, chỉ cần viết DẠNG văn bản mà câu trả lời sẽ có.

Quy tắc:
- Viết như thể bạn đang TRẢ LỜI câu hỏi (không nói "Câu trả lời sẽ bao gồm...")
- Sử dụng các từ khóa và thuật ngữ liên quan
- Giữ phong cách giống văn bản {context}
- Ngắn gọn, súc tích (100-200 từ)

Đoạn văn:"""

        try:
            logger.info(f"[HYDE] Generating hypothetical document for: {query[:60]}...")

            response = self.llm.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )

            hypothetical_doc = response.choices[0].message.content.strip()
            logger.info(f"[HYDE] Generated ({len(hypothetical_doc)} chars): {hypothetical_doc[:100]}...")

            return hypothetical_doc

        except Exception as e:
            logger.error(f"[HYDE] Error generating hypothetical document: {e}")
            logger.warning(f"[HYDE] Falling back to original query")
            return query
