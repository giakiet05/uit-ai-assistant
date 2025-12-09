"""
gRPC Server for UIT AI Assistant Agent.

This server exposes the UITAgent via gRPC for the Go backend to call.

Architecture:
    Go Backend (port 8080)
        ↓ gRPC call
    Agent gRPC Server (port 50051)
        ↓ uses
    UITAgent → ReActAgent → MCP Tools

Workflow:
1. Start MCP server: uv run python -m src.mcp.retrieval_server (port 8000)
2. Start gRPC server: uv run python -m src.grpc.agent_server (port 50051)
3. Go backend calls gRPC to get AI responses
"""

import grpc
from grpc_reflection.v1alpha import reflection
from concurrent import futures
import json
import asyncio

# LlamaIndex imports
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage as LlamaChatMessage, MessageRole

# Generated stubs
from . import agent_pb2, agent_pb2_grpc

# Agent imports
from ..core.agent import UITAgent, SharedResources
from ..config.settings import settings


class AgentServicer(agent_pb2_grpc.AgentServicer):
    """
    gRPC Servicer implementation.

    Responsibilities:
    1. Nhận ChatRequest từ Go backend
    2. Rebuild ChatMemoryBuffer từ history
    3. Tạo UITAgent instance (lightweight, stateless)
    4. Gọi agent.chat() để lấy response
    5. Map AgentResponse → protobuf ChatResponse
    6. Trả về cho Go backend
    """

    def __init__(self, resources: SharedResources):
        """
        Initialize servicer với SharedResources.

        Args:
            resources: Singleton chứa LLM + MCP tools (đã load sẵn)
        """
        self.resources = resources
        print("[Agent Servicer] Initialized with shared resources")

    async def Chat(self, request, context):
        """
        Handle Chat request (non-streaming).

        Args:
            request: ChatRequest (message + history)
            context: gRPC context

        Returns:
            ChatResponse (content + metadata)
        """
        try:
            print(f"\n{'='*60}")
            print(f"[gRPC] Received Chat request")
            print(f"[gRPC] Message: {request.message}")
            print(f"[gRPC] History length: {len(request.history)}")
            print(f"{'='*60}")

            # Step 1: Rebuild ChatMemoryBuffer từ history
            memory = ChatMemoryBuffer.from_defaults(
                token_limit=settings.chat.MEMORY_TOKEN_LIMIT,
                llm=self.resources.llm
            )

            for msg in request.history:
                memory.put(LlamaChatMessage(
                    role=MessageRole(msg.role),  # "user" hoặc "assistant"
                    content=msg.content
                ))

            print(f"[gRPC] Rebuilt memory with {len(request.history)} messages")

            # Step 2: Tạo UITAgent instance (lightweight, stateless)
            agent = UITAgent(self.resources)

            # Step 3: Gọi agent.chat()
            print(f"[gRPC] Calling UITAgent.chat()...")
            agent_response = await agent.chat(request.message, memory)

            print(f"[gRPC] Got response from agent")
            print(f"[gRPC] Content length: {len(agent_response.content)} chars")
            print(f"[gRPC] Tool calls: {len(agent_response.tool_calls)}")
            print(f"[gRPC] Sources: {len(agent_response.sources)}")

            # Step 4: Convert AgentResponse → protobuf ChatResponse
            pb_tool_calls = [
                agent_pb2.ToolCall(
                    tool_name=tc.tool_name,
                    args_json=json.dumps(tc.args),
                    output=tc.output
                )
                for tc in agent_response.tool_calls
            ]

            pb_sources = [
                agent_pb2.Source(
                    title=src.title,
                    content=src.content,
                    score=src.score,
                    url=src.url
                )
                for src in agent_response.sources
            ]

            response = agent_pb2.ChatResponse(
                content=agent_response.content,
                tool_calls=pb_tool_calls,
                reasoning_steps=agent_response.reasoning_steps,
                sources=pb_sources,
                tokens_used=agent_response.tokens_used or 0,
                latency_ms=agent_response.latency_ms or 0
            )

            print(f"[gRPC] Returning response to Go backend\n")
            return response

        except Exception as e:
            print(f"[gRPC ERROR] {e}")
            import traceback
            traceback.print_exc()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Agent error: {str(e)}")
            return agent_pb2.ChatResponse(content=f"Error: {str(e)}")


async def serve():
    """
    Start gRPC server.

    Workflow:
    1. Initialize SharedResources (load LLM)
    2. Load MCP tools asynchronously
    3. Create AgentServicer với resources
    4. Start gRPC server on port 50051
    5. Wait for termination
    """
    print("\n" + "="*60)
    print("UIT AI Assistant - Agent gRPC Server")
    print("="*60)

    # Step 1: Initialize SharedResources
    print("\n[Startup] Initializing SharedResources...")
    resources = SharedResources()

    # Step 2: Load MCP tools
    print("[Startup] Loading MCP tools from retrieval server...")
    print("[Startup] Make sure MCP server is running at http://127.0.0.1:8000/mcp")
    print("[Startup] Start it with: uv run python -m src.mcp.retrieval_server\n")

    await resources.load_tools_async()

    if not resources.tools:
        print("\n[WARNING] No tools loaded! Agent will run without retrieval capabilities.")
        print("[WARNING] Check if MCP server is running.\n")
    else:
        print(f"\n[Startup] ✅ Loaded {len(resources.tools)} tools successfully\n")

    # Step 3: Create gRPC server
    print("[Startup] Starting gRPC server on port 50051...")
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),  # 50MB
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),  # 50MB
        ]
    )

    # Step 4: Add servicer
    agent_pb2_grpc.add_AgentServicer_to_server(
        AgentServicer(resources),
        server
    )

    # Step 5: Enable reflection (for grpcurl)
    SERVICE_NAMES = (
        agent_pb2.DESCRIPTOR.services_by_name['Agent'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    # Step 6: Bind port
    server.add_insecure_port('[::]:50051')
    await server.start()

    print("\n" + "="*60)
    print("✅ gRPC Server is ready!")
    print("   Listening on: localhost:50051")
    print("   Service: agent.Agent")
    print("   Method: Chat")
    print("   Reflection: Enabled")
    print("="*60)
    print("\nPress Ctrl+C to stop the server\n")

    # Step 7: Wait for termination
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n\n[Shutdown] Received Ctrl+C, stopping server...")
        await server.stop(grace=5)
        print("[Shutdown] Server stopped gracefully\n")

