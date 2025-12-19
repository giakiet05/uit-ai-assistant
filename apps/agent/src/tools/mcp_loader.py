"""
Load MCP tools from retrieval server using langchain-mcp-adapters.
"""

from langchain_mcp_adapters.client import MultiServerMCPClient
from src.config.settings import settings


async def load_mcp_tools():
    """
    Load MCP tools from retrieval server.

    Returns:
        List of LangChain tools loaded from MCP server

    Raises:
        Exception: If MCP server is not reachable
    """
    # Get MCP server URL from settings (supports both local and Docker)
    mcp_url = settings.mcp.SERVER_URL

    # Configure MCP client for retrieval server
    client = MultiServerMCPClient({
        "uit": {
            "transport": "streamable-http",
            "url": mcp_url,
        }
    })

    try:
        print(f"[MCP LOADER] Connecting to MCP server at {mcp_url}")

        # Get tools from server
        tools = await client.get_tools()

        print(f"[MCP LOADER] ✅ Loaded {len(tools)} tools from MCP server:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:80]}...")

        return tools

    except Exception as e:
        print(f"[MCP LOADER] ❌ Failed to load MCP tools: {e}")
        print(f"[MCP LOADER] Make sure MCP server is running at {mcp_url}")
        print("[MCP LOADER] Start it with: cd apps/mcp-server && uv run python main.py")
        raise
