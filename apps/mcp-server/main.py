"""
MCP Server for UIT AI Assistant.

Exposes tools for:
- Document retrieval from UIT knowledge base
- DAA portal scraping (grades, schedule)

MCP Protocol: https://modelcontextprotocol.io/
FastMCP: https://github.com/jlowin/fastmcp
"""
from fastmcp import FastMCP

# Import from src package
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.tools.retrieval_tools import register_retrieval_tools
from src.tools.daa_scraping_tools import register_daa_tools

# Initialize FastMCP server
mcp_server = FastMCP("UIT MCP Server")

# Register all tools
print("[MCP SERVER] Registering tools...")
register_retrieval_tools(mcp_server)
register_daa_tools(mcp_server)
print("[MCP SERVER] All tools registered successfully")

if __name__ == "__main__":
    print("[MCP SERVER] Starting UIT MCP Server...")
    mcp_server.run("streamable-http")
