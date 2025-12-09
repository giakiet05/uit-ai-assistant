"""
Inspect what messages are stored in ChatMemoryBuffer after agent run.
"""

import asyncio
from src.shared.agent import AgentService


async def main():
    print("="*70)
    print("Memory Inspection Test")
    print("="*70)

    agent_service = AgentService()
    await agent_service.load_tools()

    # Ask a factual question (will call tool)
    print("\nAsking question that requires tool call...")
    result = await agent_service.chat(
        message="Điều kiện tốt nghiệp của UIT là gì?",
        session_id="memory_test"
    )

    print(f"\n[RESPONSE]: {result['response'][:200]}...\n")

    # Inspect stored messages
    history = agent_service.get_history("memory_test")

    print("="*70)
    print(f"STORED MESSAGES: {len(history)} messages")
    print("="*70)

    for i, msg in enumerate(history, 1):
        role = msg['role']
        content = msg['content']

        # Check if this is a tool output message
        is_tool_output = (
            "Retrieved" in content[:100] or
            "Document 1" in content[:100] or
            "Score:" in content[:100]
        )

        print(f"\n[Message {i}] Role: {role}")
        print(f"Is Tool Output: {is_tool_output}")
        print(f"Length: {len(content)} characters (~{len(content)//4} tokens)")
        print(f"Preview: {content[:150]}...")
        print("-" * 70)


if __name__ == "__main__":
    asyncio.run(main())
