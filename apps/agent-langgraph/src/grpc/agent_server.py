"""
gRPC server for LangGraph agent.

This server:
1. Loads LangGraph agent with checkpointer for state persistence
2. Receives requests with user_id + thread_id (no history needed)
3. Uses thread_id to load conversation state from checkpointer
4. Invokes agent graph with state management
5. Returns response to API server (which stores in MongoDB for UI)
"""

import asyncio
from concurrent import futures
import grpc

from src.config.llm_provider import create_llm
from src.config.settings import settings
from src.tools.mcp_loader import load_mcp_tools
from src.tools.credential_tool import get_user_credential
from src.graph.agent_graph import create_agent_graph
from src.graph.checkpointer import create_checkpointer
from src.grpc.pb import agent_pb2, agent_pb2_grpc


class AgentServicer(agent_pb2_grpc.AgentServicer):
    """gRPC servicer for agent with LangGraph state management."""

    def __init__(self, graph):
        """
        Initialize agent servicer.

        Args:
            graph: Compiled LangGraph agent with checkpointer
        """
        self.graph = graph
        print("[AGENT SERVER] AgentServicer initialized")

    def Chat(self, request, context):
        """
        Handle chat request (stateful with LangGraph checkpointer).

        Args:
            request: ChatRequest with message, user_id, thread_id
            context: gRPC context

        Returns:
            ChatResponse with agent's reply
        """
        print(f"\n{'='*70}")
        print(f"[AGENT SERVER] Received request:")
        print(f"  - User ID: {request.user_id}")
        print(f"  - Thread ID: {request.thread_id}")
        print(f"  - Message: {request.message[:100]}...")
        print(f"{'='*70}\n")

        try:
            # Run async graph invocation in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(
                self._ainvoke_agent(request.message, request.user_id, request.thread_id)
            )
            loop.close()

            return response

        except Exception as e:
            print(f"[AGENT SERVER] Error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Agent error: {str(e)}")
            return agent_pb2.ChatResponse(content=f"Xin lỗi, đã xảy ra lỗi: {str(e)}")

    async def _ainvoke_agent(self, message: str, user_id: str, thread_id: str):
        """
        Invoke agent graph asynchronously.

        Args:
            message: User's message
            user_id: User ID (for credential lookup)
            thread_id: Thread ID (for state persistence)

        Returns:
            ChatResponse protobuf message
        """
        # Build config with thread_id for checkpointer
        config = {"configurable": {"thread_id": thread_id}}

        # Invoke graph (will automatically load state from checkpointer if exists)
        result = await self.graph.ainvoke(
            {
                "messages": [("user", message)],
                "user_id": user_id
            },
            config=config
        )

        # Extract agent's response (last message)
        agent_message = result["messages"][-1]
        content = agent_message.content

        print(f"\n[AGENT SERVER] Response sent:")
        print(f"  - Content length: {len(content)} chars")
        print(f"  - Preview: {content[:200]}...")

        # Build ChatResponse
        return agent_pb2.ChatResponse(
            content=content,
            tool_calls=[],  # TODO: Extract tool calls from messages if needed
            reasoning_steps=[],
            sources=[],
            tokens_used=0,  # TODO: Add token counting
            latency_ms=0
        )


async def _initialize_agent():
    """
    Initialize LangGraph agent with all components.

    Returns:
        Compiled graph ready for invocation
    """
    print("\n" + "="*70)
    print("Initializing LangGraph Agent Server")
    print("="*70 + "\n")

    # Step 1: Create LLM
    print("[1/5] Creating LLM...")
    llm = create_llm(
        provider=settings.llm.PROVIDER,
        model=settings.llm.MODEL,
        temperature=0.7
    )
    print(f"✅ LLM created: {settings.llm.PROVIDER}/{settings.llm.MODEL}\n")

    # Step 2: Load MCP tools
    print("[2/5] Loading MCP tools...")
    try:
        mcp_tools = await load_mcp_tools()
        print(f"✅ MCP tools loaded: {len(mcp_tools)} tools\n")
    except Exception as e:
        print(f"⚠️  MCP tools failed to load: {e}")
        print("⚠️  Continuing with native tools only...\n")
        mcp_tools = []

    # Step 3: Add native tools
    print("[3/5] Adding native tools...")
    native_tools = [get_user_credential]
    all_tools = mcp_tools + native_tools
    print(f"✅ Total tools: {len(all_tools)}")
    print(f"   - MCP tools: {len(mcp_tools)}")
    print(f"   - Native tools: {len(native_tools)}\n")

    # Step 4: Create checkpointer
    print("[4/5] Creating checkpointer...")
    try:
        # Use MemorySaver for development (switch to PostgresSaver for production)
        checkpointer = create_checkpointer(backend="memory")
        print("✅ Checkpointer created\n")
    except Exception as e:
        print(f"⚠️  Checkpointer failed: {e}")
        print("⚠️  Running without persistence...\n")
        checkpointer = None

    # Step 5: Create agent graph
    print("[5/5] Creating agent graph...")
    graph = create_agent_graph(
        llm=llm,
        tools=all_tools,
        checkpointer=checkpointer
    )
    print("✅ Agent graph created\n")

    print("="*70)
    print("✅ Agent server initialization complete!")
    print("="*70 + "\n")

    return graph


def serve():
    """Start gRPC server."""
    # Initialize agent (runs async initialization)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    graph = loop.run_until_complete(_initialize_agent())
    loop.close()

    # Create gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    agent_pb2_grpc.add_AgentServicer_to_server(
        AgentServicer(graph),
        server
    )

    # Bind to port
    port = settings.grpc.PORT
    server.add_insecure_port(f"[::]:{port}")

    print(f"[AGENT SERVER] Starting gRPC server on port {port}...")
    server.start()
    print(f"[AGENT SERVER] ✅ Server running on port {port}\n")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n[AGENT SERVER] Shutting down...")
        server.stop(0)


if __name__ == "__main__":
    serve()
