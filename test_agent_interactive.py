"""
Interactive chat loop for testing UITAgent.

This allows you to manually test the agent and see its reasoning process.
"""

import asyncio
from src.engines.agent import AgentService


async def main():
    print("="*70)
    print("UITAgent Interactive Chat (với ReActAgent)")
    print("="*70)

    # Initialize agent service
    print("\n[INIT] Initializing AgentService...")
    agent_service = AgentService()

    # Load MCP tools
    print("\n[INIT] Loading MCP tools...")
    await agent_service.load_tools()

    print(f"\n[INIT] Agent ready with {len(agent_service.resources.tools)} tools")
    print("="*70)

    # Session ID
    session_id = "interactive_session"

    print("\nCommands:")
    print("  - Type your question to chat")
    print("  - Type '/history' to see conversation history")
    print("  - Type '/reset' to reset session")
    print("  - Type '/quit' or '/exit' to exit")
    print("="*70)

    # Chat loop
    while True:
        try:
            # Get user input
            user_input = input("\n[YOU]: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ['/quit', '/exit']:
                print("\n[SYSTEM] Goodbye!")
                break

            elif user_input.lower() == '/reset':
                agent_service.reset_session(session_id)
                print("\n[SYSTEM] Session reset!")
                continue

            elif user_input.lower() == '/history':
                history = agent_service.get_history(session_id)
                print(f"\n[SYSTEM] History ({len(history)} messages):")
                for i, msg in enumerate(history, 1):
                    role = msg['role'].upper()
                    content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                    print(f"  {i}. [{role}]: {content}")
                continue

            # Chat with agent
            print("\n[AGENT] Thinking...")
            print("-" * 70)

            result = await agent_service.chat(
                message=user_input,
                session_id=session_id,
                return_metadata=True
            )

            print("-" * 70)
            print(f"\n[AGENT]: {result['response']}\n")

            # Show metadata
            metadata = result.get('metadata', {})
            if metadata:
                print(f"[METADATA] History: {metadata.get('history_messages', 0)} messages, "
                      f"New: {metadata.get('new_messages', 0)} messages")

        except KeyboardInterrupt:
            print("\n\n[SYSTEM] Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
