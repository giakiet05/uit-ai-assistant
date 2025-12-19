# Agent Service

LangGraph-based conversational agent for UIT AI Assistant.

## Architecture

- **Framework**: LangGraph (stateful agent with checkpointer)
- **LLM**: OpenAI GPT-4.1 / Google Gemini 2.0 Flash
- **State Management**: Thread-based memory with checkpointer
- **Tools**: MCP tools (retrieval, DAA scraping) + credential lookup

## Features

- Stateful multi-turn conversations
- Tool calling (retrieve documents, scrape DAA)
- Query refinement (acronym expansion)
- Cookie-based authentication via Redis

## Usage

```bash
# Install dependencies
uv sync

# Run gRPC server
uv run python main.py
```

Server runs on port `50051` (gRPC).

## Configuration

Create `.env` file:

```
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1-mini
OPENAI_API_KEY=your_key
GRPC_PORT=50051
REDIS_URL=redis://localhost:6379/0
```
