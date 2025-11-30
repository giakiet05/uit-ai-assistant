"""
MCP Server for Document Retrieval Tool (using FastMCP).

This server exposes the QueryEngine as an MCP tool that can be used by:
- ReActAgent in ChatEngine
- External MCP clients (Claude Desktop, etc.)

MCP Protocol: https://modelcontextprotocol.io/
FastMCP: https://github.com/jlowin/fastmcp
"""
import chromadb
from fastmcp import FastMCP

from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings as LlamaSettings

from src.config.settings import settings
from src.engines.retriever.query_engine import QueryEngine
from src.engines.routing import create_router
from src.scraper.daa_scraper import DaaScraper
from src.scraper.models import Grades, Schedule

# Initialize FastMCP server
mcp = FastMCP("UIT MCP Server") # RENAMED SERVER

# Global QueryEngine instance (lazy loaded)
_query_engine = None


def _get_query_engine() -> QueryEngine:
    """
    Lazy load QueryEngine (only when first request comes).

    Returns:
        QueryEngine instance
    """
    global _query_engine

    if _query_engine is not None:
        return _query_engine

    print("[MCP SERVER] Loading QueryEngine...")

    # Setup LlamaIndex global settings
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
        print(f"[MCP SERVER] Loading collection: {category}")
        chroma_collection = db.get_or_create_collection(category)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        collections[category] = VectorStoreIndex.from_vector_store(vector_store)

    # Create router (from settings)
    print(f"[MCP SERVER] Creating router with strategy: {settings.query_routing.STRATEGY}")
    router = create_router(
        strategy=settings.query_routing.STRATEGY,
        available_collections=settings.query_routing.AVAILABLE_COLLECTIONS
    )

    # Initialize QueryEngine with router
    _query_engine = QueryEngine(
        collections=collections,
        router=router,  # Pass router to QueryEngine
        use_reranker=True,  # Enable reranker by default
        top_k=3,
        retrieval_top_k=20,
        rerank_score_threshold=0.9,  # Filter out low-confidence results after reranking
        min_score_threshold=settings.retrieval.MINIMUM_SCORE_THRESHOLD,
        use_modal=True  # Set to True to use Modal GPU for reranking (faster)
    )

    print(f"[MCP SERVER] QueryEngine loaded with {len(collections)} collections")

    return _query_engine


@mcp.tool()
def retrieve_documents(query: str) -> str:
    """
    Retrieve relevant documents from the UIT knowledge base.

    Uses blended retrieval combining:
    - Dense vector search (semantic similarity)
    - BM25 keyword search (coming soon)
    - Sparse vector search (coming soon)

    Results are automatically merged, deduplicated, and reranked for best accuracy.

    Use this when you need factual information about:
    - UIT academic regulation documents (quy định, quy chế)
    - Curriculum and program requirements (chương trình đào tạo)
    - Admission policies (tuyển sinh)
    - Graduation requirements (tốt nghiệp)

    Always use this tool BEFORE answering factual questions about UIT.

    Args:
        query: The search query (in Vietnamese or English)

    Returns:
        Clean text with retrieved documents (suitable for agent consumption)
    """
    # Get query engine
    query_engine = _get_query_engine()

    # Blended retrieval (no method selection)
    result = query_engine.retrieve_with_metadata(query)

    # Format response for agent consumption (clean, structured)
    lines = [
        f"Retrieved {result['final_count']} relevant documents for query: {result['query']}",
        ""
    ]

    for i, doc in enumerate(result['documents'], 1):
        lines.append(f"Document {i} (Score: {doc['score']:.3f}):")
        lines.append(f"{doc['text']}")
        lines.append("")  # Blank line between documents

    return "\n".join(lines)


@mcp.tool()
async def get_grades(username: str, password: str) -> Grades:
    """
    Retrieve student grades from the DAA portal.

    Returns structured grade data including:
    - Student information (name, MSSV, class, faculty, etc.)
    - Semester-by-semester breakdown with courses and GPA
    - Overall GPA summary (both 10-scale and 4-scale)

    This tool automatically calculates GPA for each semester and cumulative GPA.

    Args:
        username: The student's DAA username (MSSV).
        password: The student's DAA password.

    Returns:
        Grades: Pydantic model with complete grade information and GPA calculations.
            FastMCP will automatically generate JSON schema from this model.
    """
    async with DaaScraper(username=username, password=password, headless=True) as scraper:
        grades = await scraper.get_grades()
        return grades


@mcp.tool()
async def get_schedule(username: str, password: str) -> Schedule:
    """
    Retrieve student schedule from the DAA portal.

    Returns structured schedule data including:
    - Current semester information
    - List of all classes with details (time, room, subject, class size, etc.)
    - Day of week, period, date range for each class

    Args:
        username: The student's DAA username (MSSV).
        password: The student's DAA password.

    Returns:
        Schedule: Pydantic model with complete schedule information.
            FastMCP will automatically generate JSON schema from this model.
    """
    async with DaaScraper(username=username, password=password, headless=True) as scraper:
        schedule = await scraper.get_schedule()
        return schedule


# Entry point for running the server
if __name__ == "__main__":
    mcp.run(transport="streamable-http")