# MCP Server

MCP (Model Context Protocol) server providing tools for UIT AI Assistant.

## Tools

### Retrieval Tools
- `retrieve_regulation`: Retrieve information from university regulations
- `retrieve_curriculum`: Retrieve curriculum information for specific majors

### DAA Scraping Tools
- `get_grades`: Scrape student grades from DAA
- `get_schedule`: Scrape student schedule from DAA

## Usage

```bash
# Install dependencies
uv sync

# Run server
uv run python main.py
```

Server runs on `http://localhost:8000` with MCP streamable HTTP transport.
