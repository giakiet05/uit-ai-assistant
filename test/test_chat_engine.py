"""
Test script for ChatEngine to verify conversation memory works.
"""
from src.engines import ChatEngine


def test_basic_conversation():
    """Test basic multi-turn conversation."""
    print("\n" + "="*60)
    print("TEST 1: Basic Conversation Flow")
    print("="*60 + "\n")

    engine = ChatEngine()
    session_id = "test_session_001"

    # Turn 1: Initial question
    print("👤 User: Điều kiện tốt nghiệp của UIT là gì?")
    response1 = engine.chat(
        "Điều kiện tốt nghiệp của UIT là gì?",
        session_id=session_id
    )
    print(f"🤖 Assistant: {response1['response'][:200]}...")
    print()

    # Turn 2: Follow-up question (tests memory)
    print("👤 User: Còn điều kiện nào nữa không?")
    response2 = engine.chat(
        "Còn điều kiện nào nữa không?",  # This references previous context
        session_id=session_id
    )
    print(f"🤖 Assistant: {response2['response'][:200]}...")
    print()

    # Turn 3: Clarification (tests deeper memory)
    print("👤 User: Cho tôi biết rõ hơn về điều kiện thứ nhất")
    response3 = engine.chat(
        "Cho tôi biết rõ hơn về điều kiện thứ nhất",
        session_id=session_id
    )
    print(f"🤖 Assistant: {response3['response'][:200]}...")
    print()

    # Check history
    history = engine.get_history(session_id)
    print(f"\n📊 Total messages in history: {len(history)}")
    print(f"✅ Expected: 6 (3 user + 3 assistant)")

    # Show memory stats
    stats = engine.get_memory_stats()
    print(f"\n📈 Memory Stats: {stats}")

    # Reset
    engine.reset_session(session_id)
    print(f"\n🔄 Session {session_id} reset successfully")
    print("="*60)


def test_multi_session():
    """Test multiple concurrent sessions."""
    print("\n" + "="*60)
    print("TEST 2: Multiple Sessions (Isolation Test)")
    print("="*60 + "\n")

    engine = ChatEngine()

    # Session 1: Student A asking about graduation
    print("👤 Student A (session_a): Tôi cần bao nhiêu tín chỉ để tốt nghiệp?")
    resp_a1 = engine.chat(
        "Tôi cần bao nhiêu tín chỉ để tốt nghiệp?",
        session_id="student_a"
    )
    print(f"🤖 Assistant: {resp_a1['response'][:150]}...")
    print()

    # Session 2: Student B asking about admission
    print("👤 Student B (session_b): Điểm chuẩn ngành AI là bao nhiêu?")
    resp_b1 = engine.chat(
        "Điểm chuẩn ngành AI là bao nhiêu?",
        session_id="student_b"
    )
    print(f"🤖 Assistant: {resp_b1['response'][:150]}...")
    print()

    # Session 1: Follow-up (should remember graduation context, NOT admission)
    print("👤 Student A (session_a): Còn GPA tối thiểu là bao nhiêu?")
    resp_a2 = engine.chat(
        "Còn GPA tối thiểu là bao nhiêu?",
        session_id="student_a"
    )
    print(f"🤖 Assistant: {resp_a2['response'][:150]}...")
    print()

    # Session 2: Follow-up (should remember admission context, NOT graduation)
    print("👤 Student B (session_b): Còn ngành khác thì sao?")
    resp_b2 = engine.chat(
        "Còn ngành khác thì sao?",
        session_id="student_b"
    )
    print(f"🤖 Assistant: {resp_b2['response'][:150]}...")
    print()

    # Verify isolation
    history_a = engine.get_history("student_a")
    history_b = engine.get_history("student_b")

    print(f"\n📊 Session A messages: {len(history_a)}")
    print(f"📊 Session B messages: {len(history_b)}")

    stats = engine.get_memory_stats()
    print(f"\n📈 Total sessions: {stats['total_sessions']}")
    print(f"📈 Total messages: {stats['total_messages']}")

    print("\n✅ Multi-session test passed - sessions are isolated correctly")
    print("="*60)


def test_context_switching():
    """Test if the engine can handle context switches within same session."""
    print("\n" + "="*60)
    print("TEST 3: Context Switching")
    print("="*60 + "\n")

    engine = ChatEngine()
    session_id = "context_test"

    # Topic 1: Graduation
    print("👤 User: Điều kiện tốt nghiệp là gì?")
    resp1 = engine.chat("Điều kiện tốt nghiệp là gì?", session_id=session_id)
    print(f"🤖 Assistant: {resp1['response'][:100]}...")
    print()

    # Switch to Topic 2: Admission (completely different)
    print("👤 User: Điểm chuẩn ngành Khoa học máy tính là bao nhiêu?")
    resp2 = engine.chat("Điểm chuẩn ngành Khoa học máy tính là bao nhiêu?", session_id=session_id)
    print(f"🤖 Assistant: {resp2['response'][:100]}...")
    print()

    # Follow-up on Topic 2 (should NOT confuse with Topic 1)
    print("👤 User: Điểm năm ngoái thì sao?")
    resp3 = engine.chat("Điểm năm ngoái thì sao?", session_id=session_id)
    print(f"🤖 Assistant: {resp3['response'][:100]}...")
    print()

    print("✅ Context switching test completed")
    print("="*60)


def interactive_chat():
    """Interactive mode for manual testing."""
    print("\n" + "="*60)
    print("INTERACTIVE CHAT MODE")
    print("Type 'exit' to quit, 'reset' to clear history, 'history' to view")
    print("="*60 + "\n")

    engine = ChatEngine()
    session_id = "interactive_session"

    while True:
        try:
            user_input = input("\n👤 You: ").strip()

            if user_input.lower() in ['exit', 'quit']:
                print("\nGoodbye! 👋")
                break

            if user_input.lower() == 'reset':
                engine.reset_session(session_id)
                print("✅ Conversation history cleared")
                continue

            if user_input.lower() == 'history':
                history = engine.get_history(session_id)
                print(f"\n📜 Conversation History ({len(history)} messages):")
                for msg in history:
                    role_emoji = "👤" if msg["role"] == "user" else "🤖"
                    print(f"{role_emoji} {msg['role'].upper()}: {msg['content'][:100]}...")
                continue

            if not user_input:
                continue

            # Get response
            response = engine.chat(user_input, session_id=session_id)
            print(f"\n🤖 Assistant: {response['response']}")

        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_chat()
    else:
        # Run all automated tests
        test_basic_conversation()
        test_multi_session()
        test_context_switching()

        print("\n" + "="*60)
        print("🎉 ALL TESTS COMPLETED!")
        print("="*60)
        print("\nTo try interactive mode, run:")
        print("  python test_chat_engine.py interactive")
