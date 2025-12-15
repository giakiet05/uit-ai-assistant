"""
Load MCP tools from retrieval server using langchain-mcp-adapters.
"""

from langchain_mcp_adapters.client import MultiServerMCPClient


async def load_mcp_tools():
    """
    Load MCP tools from retrieval server.

    The MCP server must be running at http://127.0.0.1:8000/mcp
    Start it with: cd apps/mcp-server && uv run python -m src.server

    Returns:
        List of LangChain tools loaded from MCP server

    Raises:
        Exception: If MCP server is not reachable
    """
    # Configure MCP client for retrieval server
    client = MultiServerMCPClient({
        "uit": {
            "transport": "streamable-http",
            "url": "http://127.0.0.1:8000/mcp",
        }
    })

    try:
        print("[MCP LOADER] Connecting to MCP server at http://127.0.0.1:8000/mcp")

        # Get tools from server
        tools = await client.get_tools()

        print(f"[MCP LOADER] ✅ Loaded {len(tools)} tools from MCP server:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:80]}...")

        return tools

    except Exception as e:
        print(f"[MCP LOADER] ❌ Failed to load MCP tools: {e}")
        print("[MCP LOADER] Make sure MCP server is running at http://127.0.0.1:8000/mcp")
        print("[MCP LOADER] Start it with: cd apps/mcp-server && uv run python -m src.server")
        raise
