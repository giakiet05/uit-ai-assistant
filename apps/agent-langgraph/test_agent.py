"""
Test script for LangGraph agent.

Usage:
    uv run python test_agent.py
"""

import asyncio
from src.config.llm_provider import create_llm
from src.config.settings import settings
from src.tools.mcp_loader import load_mcp_tools
from src.tools.credential_tool import get_user_credential
from src.graph.agent_graph import create_agent_graph
from src.graph.checkpointer import create_checkpointer


async def main():
    print("\n" + "="*60)
    print("Testing LangGraph Agent")
    print("="*60 + "\n")

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
        # Use in-memory checkpointer for testing (faster, no DB setup needed)
        # Change to "postgres" for production testing
        checkpointer = create_checkpointer(backend="memory")
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

    # Test 1: Simple greeting (no tools)
    print("="*60)
    print("Test 1: Simple greeting")
    print("="*60)

    config = {"configurable": {"thread_id": "test-thread-1"}}
    result = await graph.ainvoke(
        {
            "messages": [("user", "Xin chào bạn")],
            "user_id": "test-user-123"
        },
        config=config
    )

    print(f"\nUser: Xin chào bạn")
    print(f"Agent: {result['messages'][-1].content}\n")

    # Test 2: Query that should call retrieval tool (if MCP is running)
    if mcp_tools:
        print("="*60)
        print("Test 2: Retrieval query")
        print("="*60)

        config = {"configurable": {"thread_id": "test-thread-2"}}
        result = await graph.ainvoke(
            {
                "messages": [("user", "Điều kiện tốt nghiệp là gì?")],
                "user_id": "test-user-123"
            },
            config=config
        )

        print(f"\nUser: Điều kiện tốt nghiệp là gì?")
        print(f"Agent: {result['messages'][-1].content[:500]}...\n")

    # Test 3: Multi-turn conversation
    print("="*60)
    print("Test 3: Multi-turn conversation (memory test)")
    print("="*60)

    thread_id = "test-thread-3"
    config = {"configurable": {"thread_id": thread_id}}

    # Turn 1
    result = await graph.ainvoke(
        {
            "messages": [("user", "Tên tao là Kiệt")],
            "user_id": "test-user-123"
        },
        config=config
    )
    print(f"\nUser: Tên tao là Kiệt")
    print(f"Agent: {result['messages'][-1].content}")

    # Turn 2 (should remember name)
    result = await graph.ainvoke(
        {
            "messages": [("user", "Tao tên gì?")],
            "user_id": "test-user-123"
        },
        config=config
    )
    print(f"\nUser: Tao tên gì?")
    print(f"Agent: {result['messages'][-1].content}\n")

    print("="*60)
    print("✅ All tests completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
