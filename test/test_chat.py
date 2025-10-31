"""
A simple script for interactively testing the ChatEngine.
"""

from src.engines import ChatEngine

def main():
    """
    Initializes the ChatEngine and enters an interactive loop to accept user messages.
    """
    try:
        chat_engine = ChatEngine()
    except Exception as e:
        print(f"[FATAL] Failed to initialize ChatEngine: {e}")
        return

    print("\n" + "="*50)
    print("✅ Chat Engine is ready. Type 'exit' or 'quit' to stop.")
    print("="*50)

    # Example questions you can ask:
    print("\nExample questions:")
    print(" - Điều kiện tốt nghiệp là gì?")
    print(" - Còn điều kiện nào nữa?")
    print(" - Cho tôi biết rõ hơn về điều kiện thứ nhất")
    print(" - ...")

    print("\nSpecial commands:")
    print(" - 'reset'   : Clear conversation history")
    print(" - 'history' : View conversation history")
    print(" - 'exit'    : Exit the program")

    session_id = "default_session"

    while True:
        try:
            question = input("\n💬 Your Message: ")

            if question.lower() in ['exit', 'quit']:
                break

            if not question:
                continue

            # Handle special commands
            if question.lower() == 'reset':
                chat_engine.reset_session(session_id)
                print("✅ Conversation history cleared.")
                continue

            if question.lower() == 'history':
                history = chat_engine.get_history(session_id)
                if not history:
                    print("📜 No conversation history yet.")
                else:
                    print(f"\n📜 Conversation History ({len(history)} messages):")
                    print("-" * 50)
                    for msg in history:
                        role_emoji = "👤" if msg["role"] == "user" else "🤖"
                        print(f"{role_emoji} {msg['role'].upper()}: {msg['content']}")
                        print("-" * 50)
                continue

            # Get response from chat engine
            result = chat_engine.chat(
                message=question,
                session_id=session_id,
                return_source_nodes=True
            )

            print("\n" + "-"*3)
            print(f"🤖 Answer: {result['response']}")
            print("-"*3)

            # Print source nodes for verification
            if 'source_nodes' in result and result['source_nodes']:
                print("📚 Sources:")
                for i, source_node in enumerate(result['source_nodes']):
                    print(f"  [{i+1}] Score: {source_node.score:.4f}")
                    # Access metadata that we attached during the build process
                    if 'original_url' in source_node.metadata:
                        print(f"      - URL: {source_node.metadata['original_url']}")
                    if 'title' in source_node.metadata:
                        print(f"      - Title: {source_node.metadata['title']}")
            else:
                print("📚 No sources found.")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"[ERROR] An error occurred: {e}")

if __name__ == "__main__":
    main()
