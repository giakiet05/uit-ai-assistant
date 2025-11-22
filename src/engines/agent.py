"""
UITAgent - ReActAgent-based chatbot with MCP tools integration.

Uses stateless architecture with dependency injection:
- SharedResources: Heavy resources initialized once (LLM, collections, MCP tools)
- UITAgent: Lightweight agent created per request, using injected resources

Architecture:
    SharedResources (global, singleton)
        ↓ inject
    UITAgent (stateless, per-request)
        ↓ uses
    ReActAgent (with MCP tools + ChatMemoryBuffer)
"""

from typing import List, Optional
from datetime import datetime

# LlamaIndex imports
from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage


# MCP imports
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec

# Config
from src.config.settings import settings

# Memory
from src.engines.memory import InMemoryStore

from src.llm.provider import create_llm

class SharedResources:
    """
    Shared resources initialized once at startup.

    Contains heavy resources that should be reused across requests:
    - LLM instance
    - MCP tools (from retrieval server)
    - System prompt

    This class implements the "expensive initialization once" pattern
    for dependency injection.
    """

    SYSTEM_PROMPT = """
Bạn là trợ lý AI chuyên gia về lĩnh vực giáo dục đại học tại Trường Đại học Công nghệ Thông tin (UIT).

⚠️ QUY TẮC BẮT BUỘC:

1. KHI NÀO GỌI TOOL:
   - Khi user hỏi về QUY ĐỊNH, CHƯƠNG TRÌNH ĐÀO TẠO, TUYỂN SINH, TỐT NGHIỆP
   → PHẢI gọi tool retrieve_documents() TRƯỚC KHI trả lời

   - Khi user chào hỏi, hỏi chung chung, hoặc hỏi về bạn
   → Trả lời trực tiếp, KHÔNG cần gọi tool

2. KHI TRẢ LỜI TỪ TOOL:
   - CHỈ sử dụng thông tin từ tool retrieve_documents()
   - TUYỆT ĐỐI KHÔNG bịa đặt hoặc thêm thông tin không có
   - Nếu không tìm thấy thông tin → Nói rõ "Tôi không tìm thấy thông tin này"

3. LUÔN TRẢ LỜI BẰNG TIẾNG VIỆT.

Examples:
- "Điều kiện tốt nghiệp là gì?" → Gọi tool retrieve_documents
- "Xin chào bạn" → Trả lời trực tiếp
- "Bạn có thể giúp gì?" → Trả lời trực tiếp về khả năng của bạn
- "Chương trình đào tạo KHMT có gì?" → Gọi tool retrieve_documents
"""

    def __init__(self):
        """Initialize shared resources (expensive, one-time operation)."""
        print("[SHARED RESOURCES] Initializing...")

        # 1. Initialize LLM
        print(f"[SHARED RESOURCES] Loading LLM: {settings.llm.MODEL}")
        self.llm = create_llm(settings.llm.PROVIDER, settings.llm.MODEL)

        # 2. Initialize empty tools list (will be loaded async)
        self.tools = []

        # 3. Store system prompt
        self.system_prompt = self.SYSTEM_PROMPT

        print(f"[SHARED RESOURCES] ✅ Initialized (tools will be loaded async)")

    async def load_tools_async(self) -> List:
        """
        Load tools from MCP retrieval server (async).

        The MCP server should be running separately with streamable-http transport.
        Start the server first: uv run python -m src.mcp.retrieval_server

        Returns:
            List of FunctionTool instances from MCP server
        """
        # MCP server URL (streamable-http transport)
        # Server must be started separately before loading tools
        mcp_server_url = "http://127.0.0.1:8000/mcp"

        try:
            print(f"[SHARED RESOURCES] Connecting to MCP server at {mcp_server_url}")

            # Create MCP client with HTTP URL (streamable-http transport)
            client = BasicMCPClient(mcp_server_url)
            tool_spec = McpToolSpec(client=client)

            # Load tools from server
            tools = await tool_spec.to_tool_list_async()

            print(f"[SHARED RESOURCES] Loaded {len(tools)} tools from MCP server:")
            for tool in tools:
                print(f"  - {tool.metadata.name}: {tool.metadata.description[:100]}...")

            self.tools = tools
            return tools

        except Exception as e:
            print(f"[ERROR] Failed to load MCP tools: {e}")
            import traceback
            traceback.print_exc()
            print("[WARNING] Agent will run without retrieval tools!")
            print(f"[WARNING] Make sure MCP server is running at {mcp_server_url}")
            print("[WARNING] Start it with: uv run python -m src.mcp.retrieval_server")
            return []


class UITAgent:
    """
    Stateless UIT Agent using ReActAgent.

    This agent is designed to be created per request with injected resources.
    It does not maintain state - conversation history is managed externally
    via ChatMemoryBuffer loaded from persistent storage.

    Usage:
        # Initialize shared resources once (at app startup)
        resources = SharedResources()

        # Per request:
        memory = restore_memory_from_db(session_id)
        agent = UITAgent(resources)
        response = await agent.chat(message, memory)
        save_memory_to_db(session_id, memory)
    """

    def __init__(self, resources: SharedResources):
        """
        Initialize agent with injected resources.

        This is lightweight - only creates the ReActAgent wrapper.
        No heavy initialization happens here.

        Args:
            resources: SharedResources instance with LLM, tools, etc.
        """
        self.resources = resources

        # Create ReActAgent (lightweight operation)
        self.agent = ReActAgent(
            tools=resources.tools,
            llm=resources.llm,
            system_prompt=resources.system_prompt,
            verbose=True  # For debugging
        )

    async def chat(
        self,
        message: str,
        memory: ChatMemoryBuffer
    ) -> str:
        """
        Chat with the agent (async).

        Args:
            message: User's message
            memory: ChatMemoryBuffer with conversation history

        Returns:
            Agent's response text
        """
        # Run agent with memory
        response = await self.agent.run(message, memory=memory)

        # Extract text from ChatMessage
        # response.response is a ChatMessage object, not a string
        # Get the actual text content
        if hasattr(response.response, 'content'):
            # ChatMessage has .content attribute
            response_text = response.response.content
        elif hasattr(response.response, 'blocks') and len(response.response.blocks) > 0:
            # Extract from blocks
            response_text = response.response.blocks[0].text
        else:
            # Fallback: convert to string
            response_text = str(response.response)

        return response_text

    async def stream_chat(
        self,
        message: str,
        memory: ChatMemoryBuffer
    ):
        """
        Stream chat response (for real-time UI updates).

        Args:
            message: User's message
            memory: ChatMemoryBuffer with conversation history

        Yields:
            AgentStream events (text deltas) or final response
        """
        from llama_index.core.agent.workflow import AgentStream

        handler = self.agent.run(message, memory=memory)

        async for ev in handler.stream_events():
            if isinstance(ev, AgentStream):
                yield ev.delta

        # Yield final response
        response = await handler
        yield ("FINAL_RESPONSE", response)


class AgentService:
    """
    Service layer for managing agents with session-based memory.

    This handles:
    - Memory persistence (load/save from DB)
    - Agent creation per request
    - Session management

    Usage in FastAPI:
        # At startup
        agent_service = AgentService()

        # Per request
        @app.post("/chat")
        async def chat(request: ChatRequest):
            response = await agent_service.chat(
                message=request.message,
                session_id=request.session_id
            )
            return {"response": response}
    """

    def __init__(self, memory_store: Optional[InMemoryStore] = None):
        """
        Initialize agent service.

        Args:
            memory_store: Persistent memory store (InMemoryStore, RedisStore, etc.)
                         If None, creates new InMemoryStore
        """
        print("[AGENT SERVICE] Initializing...")

        # 1. Initialize shared resources (expensive, one-time)
        self.resources = SharedResources()

        # 2. Initialize memory store
        self.memory_store = memory_store or InMemoryStore()

        # 3. Flag to track if tools are loaded
        self._tools_loaded = False

        print("[AGENT SERVICE] ✅ Ready (call load_tools() to load MCP tools)")

    async def load_tools(self):
        """
        Load MCP tools asynchronously.

        This should be called once after initialization in an async context.
        """
        if not self._tools_loaded:
            await self.resources.load_tools_async()
            self._tools_loaded = True

    async def chat(
        self,
        message: str,
        session_id: str = "default",
        return_metadata: bool = False
    ) -> dict:
        """
        Chat with agent for a given session.

        Handles the full lifecycle:
        1. Load conversation history from memory store
        2. Create memory buffer with history
        3. Create agent instance (stateless)
        4. Run agent
        5. Save updated history back to memory store

        Args:
            message: User's message
            session_id: Session identifier for conversation history
            return_metadata: Whether to return metadata (tool calls, etc.)

        Returns:
            dict with 'response', 'session_id', 'timestamp', optional metadata
        """
        print(f"\n{'='*60}")
        print(f"[AGENT SERVICE] Session: {session_id}")
        print(f"[AGENT SERVICE] User: {message}")
        print(f"{'='*60}")

        try:
            # 1. Load conversation history from memory store
            history = self.memory_store.get_history(
                session_id,
                max_messages=settings.chat.MAX_HISTORY_MESSAGES
            )

            print(f"[AGENT SERVICE] Loaded {len(history)} messages from history")

            # 2. Create ChatMemoryBuffer and restore history
            memory = ChatMemoryBuffer.from_defaults(
                token_limit=40000,  # Default token limit
                llm=self.resources.llm
            )

            for msg in history:
                memory.put(ChatMessage(role=msg.role, content=msg.content))

            # 3. Create agent instance (lightweight, stateless)
            agent = UITAgent(self.resources)

            # 4. Run agent
            response_text = await agent.chat(message, memory)

            # Ensure response_text is string
            if not isinstance(response_text, str):
                response_text = str(response_text)

            print(f"[AGENT SERVICE] Agent response: {response_text[:200]}...")

            # 5. Extract new messages from memory and save
            all_messages = memory.get_all()
            new_messages = all_messages[len(history):]  # Only new messages

            for msg in new_messages:
                self.memory_store.add_message(
                    session_id,
                    ChatMessage(role=msg.role, content=msg.content)
                )

            print(f"[AGENT SERVICE] Saved {len(new_messages)} new messages to memory store")

            # 6. Build response
            result = {
                "response": response_text,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }

            if return_metadata:
                result["metadata"] = {
                    "history_messages": len(history),
                    "new_messages": len(new_messages)
                }

            return result

        except Exception as e:
            print(f"[ERROR] Agent service failed: {e}")
            import traceback
            traceback.print_exc()

            error_response = "Xin lỗi, đã có lỗi xảy ra khi xử lý câu hỏi của bạn."

            return {
                "response": error_response,
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def reset_session(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        print(f"[AGENT SERVICE] Resetting session: {session_id}")
        self.memory_store.clear_session(session_id)

    def get_history(self, session_id: str) -> list:
        """Get conversation history for a session."""
        history = self.memory_store.get_history(session_id)
        return [
            {
                "role": str(msg.role),  # Convert MessageRole enum to string
                "content": msg.content
            }
            for msg in history
        ]

    def get_stats(self) -> dict:
        """Get memory store statistics."""
        return self.memory_store.get_stats()
