"""
MCP Server for Document Retrieval Tool.

This server exposes the QueryEngine as an MCP tool that can be used by:
- ReActAgent in ChatEngine
- External MCP clients (Claude Desktop, etc.)

MCP Protocol: https://modelcontextprotocol.io/
"""

import asyncio
import chromadb
from typing import Dict, Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings as LlamaSettings

from src.config.settings import settings
from src.engines.retriever.query_engine import QueryEngine


class RetrievalMCPServer:
    """MCP Server for document retrieval."""

    def __init__(self):
        """Initialize MCP server with QueryEngine."""
        self.server = Server("uit-retrieval-server")
        self.query_engine = None

        # Register tool
        self._register_tools()

        # Register handlers
        self._register_handlers()

        print("[MCP SERVER] Retrieval server initialized")

    def _load_query_engine(self):
        """Lazy load QueryEngine (only when first request comes)."""
        if self.query_engine is not None:
            return

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

        # Initialize QueryEngine
        self.query_engine = QueryEngine(
            collections=collections,
            use_reranker=True,  # Enable reranker by default
            top_k=5,
            retrieval_top_k=20
        )

        print(f"[MCP SERVER] QueryEngine loaded with {len(collections)} collections")

    def _register_tools(self):
        """Register MCP tools."""

        # Tool 1: retrieve_documents
        retrieve_tool = Tool(
            name="retrieve_documents",
            description=(
                "Retrieve relevant documents from the UIT knowledge base. "
                "This tool searches across regulations and curriculum documents. "
                "Use this when you need factual information about UIT policies, "
                "academic regulations, or curriculum details. "
                "Always use this tool BEFORE answering factual questions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (in Vietnamese or English)"
                    },
                    "method": {
                        "type": "string",
                        "enum": ["dense", "bm25", "hybrid"],
                        "description": "Retrieval method (default: dense)",
                        "default": "dense"
                    }
                },
                "required": ["query"]
            }
        )

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [retrieve_tool]

    def _register_handlers(self):
        """Register MCP request handlers."""

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
            """Handle tool calls."""

            if name == "retrieve_documents":
                # Lazy load query engine
                self._load_query_engine()

                query = arguments.get("query")
                method = arguments.get("method", "dense")

                if not query:
                    return [TextContent(
                        type="text",
                        text="Error: 'query' parameter is required"
                    )]

                # Retrieve documents
                result = self.query_engine.retrieve_with_metadata(query, method)

                # Format response
                response_text = self._format_retrieval_result(result)

                return [TextContent(
                    type="text",
                    text=response_text
                )]

            else:
                return [TextContent(
                    type="text",
                    text=f"Error: Unknown tool '{name}'"
                )]

    def _format_retrieval_result(self, result: Dict) -> str:
        """Format retrieval result as text."""
        lines = [
            f"[Retrieval Result]",
            f"Query: {result['query']}",
            f"Method: {result['method']}",
            f"Reranked: {'Yes' if result['reranked'] else 'No'}",
            f"Retrieved: {result['total_retrieved']} → Final: {result['final_count']}",
            "",
            "Documents:"
        ]

        for i, doc in enumerate(result['documents'], 1):
            lines.append(f"\n--- Document {i} (Score: {doc['score']:.4f}) ---")
            if doc['hierarchy']:
                lines.append(f"Hierarchy: {doc['hierarchy']}")
            lines.append(f"\n{doc['text'][:500]}...")  # First 500 chars

        return "\n".join(lines)

    async def run(self, transport="stdio"):
        """Run the MCP server."""
        from mcp.server.stdio import stdio_server

        print(f"[MCP SERVER] Starting server with transport: {transport}")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def main():
    """Main entry point for MCP server."""
    server = RetrievalMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
