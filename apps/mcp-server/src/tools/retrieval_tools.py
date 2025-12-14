"""
MCP tools for document retrieval from UIT knowledge base.
"""
import chromadb
from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings as LlamaSettings

from ..config.settings import settings
from ..retriever.query_engine import QueryEngine
from ..routing.router_factory import create_router
from ..retriever.schemas import (
    RegulationRetrievalResult,
    CurriculumRetrievalResult
)

# Global QueryEngine instance (lazy loaded)
_query_engine = None


def _get_query_engine() -> QueryEngine:
    """Lazy load QueryEngine."""
    global _query_engine

    if _query_engine is not None:
        return _query_engine

    print("[RETRIEVAL TOOLS] Loading QueryEngine...")

    # Setup embeddings
    if not settings.credentials.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found")

    LlamaSettings.embed_model = OpenAIEmbedding(
        model=settings.retrieval.EMBED_MODEL,
        api_key=settings.credentials.OPENAI_API_KEY
    )

    # Load ChromaDB collections
    db = chromadb.PersistentClient(path=str(settings.paths.VECTOR_STORE_DIR))

    collections = {}
    for category in settings.query_routing.AVAILABLE_COLLECTIONS:
        print(f"[RETRIEVAL TOOLS] Loading collection: {category}")
        chroma_collection = db.get_or_create_collection(category)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        collections[category] = VectorStoreIndex.from_vector_store(vector_store)

    # Create router
    print(f"[RETRIEVAL TOOLS] Creating router with strategy: {settings.query_routing.STRATEGY}")
    router = create_router(
        strategy=settings.query_routing.STRATEGY,
        available_collections=settings.query_routing.AVAILABLE_COLLECTIONS
    )

    # Initialize QueryEngine
    _query_engine = QueryEngine(
        collections=collections,
        router=router,
        use_reranker=True,
        top_k=3,
        retrieval_top_k=20,
        rerank_score_threshold=0,
        min_score_threshold=settings.retrieval.MINIMUM_SCORE_THRESHOLD,
        use_modal=True
    )

    print(f"[RETRIEVAL TOOLS] QueryEngine loaded with {len(collections)} collections")
    return _query_engine


def register_retrieval_tools(mcp: FastMCP):
    """Register retrieval tools to FastMCP instance."""

    @mcp.tool()
    def retrieve_regulation(query: str) -> ToolResult:
        """
        Retrieve regulation documents from UIT knowledge base.

        Use this when you need information about:
        - Academic regulations (quy định, quy chế)
        - Student conduct rules (quy định sinh viên)
        - Graduation requirements (điều kiện tốt nghiệp)
        - Grading policies (quy định điểm)
        - Academic policies (chính sách học vụ)

        Returns structured JSON with clean content and separated metadata fields.

        Args:
            query: The search query (in Vietnamese or English)

        Returns:
            ToolResult with JSON content and structured data
        """
        import json

        query_engine = _get_query_engine()
        result_dict = query_engine.retrieve_structured(query, collection_type="regulation")

        # Validate with Pydantic
        result_model = RegulationRetrievalResult(**result_dict)

        # Serialize to JSON for content (LangChain compatibility)
        json_content = json.dumps(result_model.model_dump(), ensure_ascii=False, indent=2)

        # Return ToolResult with both text and structured content
        return ToolResult(
            content=json_content,  # JSON string for LangChain
            structured_content=result_model.model_dump()  # Object for MCP Inspector
        )

    @mcp.tool()
    def retrieve_curriculum(query: str) -> ToolResult:
        """
        Retrieve curriculum documents from UIT knowledge base.

        Use this when you need information about:
        - Program curricula (chương trình đào tạo)
        - Course requirements (yêu cầu môn học)
        - Credit requirements (số tín chỉ)
        - Course structure (cấu trúc khóa học)
        - Major programs (các ngành đào tạo)

        Returns structured JSON with clean content and separated metadata fields.

        Args:
            query: The search query (in Vietnamese or English)

        Returns:
            ToolResult with JSON content and structured data
        """
        import json

        query_engine = _get_query_engine()
        result_dict = query_engine.retrieve_structured(query, collection_type="curriculum")

        # Validate with Pydantic
        result_model = CurriculumRetrievalResult(**result_dict)

        # Serialize to JSON for content (LangChain compatibility)
        json_content = json.dumps(result_model.model_dump(), ensure_ascii=False, indent=2)

        # Return ToolResult with both text and structured content
        return ToolResult(
            content=json_content,  # JSON string for LangChain
            structured_content=result_model.model_dump()  # Object for MCP Inspector
        )

    @mcp.tool()
    def retrieve_documents(query: str) -> str:
        """
        [DEPRECATED] Retrieve relevant documents from the UIT knowledge base.

        This tool is deprecated. Use retrieve_regulation() or retrieve_curriculum() instead
        for better routing control and structured output.

        Args:
            query: The search query (in Vietnamese or English)

        Returns:
            Clean text with retrieved documents (suitable for agent consumption)
        """
        query_engine = _get_query_engine()
        result = query_engine.retrieve_with_metadata(query)

        lines = [
            f"Retrieved {result['final_count']} relevant documents for query: {result['query']}",
            ""
        ]

        for i, doc in enumerate(result['documents'], 1):
            lines.append(f"Document {i} (Score: {doc['score']:.3f}):")
            lines.append(f"{doc['text']}")
            lines.append("")

        return "\n".join(lines)
