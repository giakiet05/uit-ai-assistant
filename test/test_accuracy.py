"""
Test accuracy of QueryEngine and ChatEngine with predefined questions.
Run this after tuning parameters to measure improvements.
"""

from src.engines import QueryEngine, ChatEngine
from typing import List, Dict, Tuple
import time


# Test cases: (question, expected_keywords, category)
TEST_CASES = [
    # Graduation requirements
    ("Điều kiện tốt nghiệp UIT là gì?",
     ["tín chỉ", "gpa", "học phí"],
     "graduation"),

    ("Cần bao nhiêu tín chỉ để tốt nghiệp?",
     ["120", "132", "tín chỉ"],
     "graduation"),

    ("GPA tối thiểu để tốt nghiệp là bao nhiêu?",
     ["gpa", "2.0", "điểm"],
     "graduation"),

    # Academic policies
    ("Quy chế đào tạo theo học chế tín chỉ là gì?",
     ["tín chỉ", "học phần", "chương trình"],
     "academic_policy"),

    ("Thời gian học tối đa là bao lâu?",
     ["năm", "học kỳ", "thời gian"],
     "academic_policy"),

    # Registration
    ("Làm thế nào để đăng ký học phần?",
     ["đăng ký", "học phần", "thời gian"],
     "registration"),

    # Fees
    ("Học phí UIT là bao nhiêu?",
     ["học phí", "đồng", "học kỳ"],
     "fees"),

    # Student life
    ("UIT có những câu lạc bộ nào?",
     ["câu lạc bộ", "sinh viên", "hoạt động"],
     "student_life"),

    # Degrees
    ("Các loại bằng tốt nghiệp tại UIT?",
     ["bằng", "tốt nghiệp", "loại"],
     "degrees"),

    # Scholarships
    ("Học bổng UIT có những loại nào?",
     ["học bổng", "sinh viên", "điều kiện"],
     "scholarships"),
]


def check_keywords(response: str, keywords: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if expected keywords appear in response.
    Returns: (all_found, missing_keywords)
    """
    response_lower = response.lower()
    missing = []

    for keyword in keywords:
        if keyword.lower() not in response_lower:
            missing.append(keyword)

    return len(missing) == 0, missing


def test_query_engine():
    """Test QueryEngine with all test cases."""
    print("\n" + "="*60)
    print("TESTING QUERY ENGINE")
    print("="*60 + "\n")

    try:
        engine = QueryEngine()
    except Exception as e:
        print(f"❌ Failed to initialize QueryEngine: {e}")
        return

    results = []
    total_time = 0

    for i, (question, keywords, category) in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}] Testing: {question}")
        print(f"Category: {category}")
        print(f"Expected keywords: {keywords}")

        start_time = time.time()

        try:
            response = engine.query(question)
            elapsed = time.time() - start_time
            total_time += elapsed

            answer = response.response
            has_answer = answer and "không tìm thấy" not in answer.lower()

            if has_answer:
                all_found, missing = check_keywords(answer, keywords)

                if all_found:
                    print("✅ PASS - All keywords found")
                    results.append(("PASS", question, category))
                else:
                    print(f"⚠️  PARTIAL - Missing keywords: {missing}")
                    results.append(("PARTIAL", question, category))
            else:
                print("❌ FAIL - No relevant answer found")
                results.append(("FAIL", question, category))

            print(f"Time: {elapsed:.2f}s")

        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append(("ERROR", question, category))

    # Summary
    print("\n" + "="*60)
    print("QUERY ENGINE SUMMARY")
    print("="*60)

    pass_count = sum(1 for r in results if r[0] == "PASS")
    partial_count = sum(1 for r in results if r[0] == "PARTIAL")
    fail_count = sum(1 for r in results if r[0] == "FAIL")
    error_count = sum(1 for r in results if r[0] == "ERROR")

    total = len(results)
    accuracy = (pass_count / total * 100) if total > 0 else 0

    print(f"\nTotal tests: {total}")
    print(f"✅ Pass: {pass_count} ({pass_count/total*100:.1f}%)")
    print(f"⚠️  Partial: {partial_count} ({partial_count/total*100:.1f}%)")
    print(f"❌ Fail: {fail_count} ({fail_count/total*100:.1f}%)")
    print(f"💥 Error: {error_count} ({error_count/total*100:.1f}%)")
    print(f"\nAccuracy Score: {accuracy:.1f}%")
    print(f"Average response time: {total_time/total:.2f}s")

    return results


def test_chat_engine():
    """Test ChatEngine with conversation scenarios."""
    print("\n" + "="*60)
    print("TESTING CHAT ENGINE")
    print("="*60 + "\n")

    try:
        engine = ChatEngine()
    except Exception as e:
        print(f"❌ Failed to initialize ChatEngine: {e}")
        return

    session_id = "accuracy_test"

    # Test conversation flow
    conversations = [
        # Scenario 1: Follow-up about graduation
        [
            ("Điều kiện tốt nghiệp là gì?", ["tín chỉ", "gpa"]),
            ("Còn điều kiện nào nữa?", ["kỷ luật", "học phí"]),
            ("Cho tôi biết rõ hơn về điều kiện thứ nhất", ["tín chỉ", "120"])
        ],
    ]

    results = []

    for conv_idx, conversation in enumerate(conversations, 1):
        print(f"\n--- Conversation {conv_idx} ---")
        engine.reset_session(session_id)

        for turn_idx, (question, keywords) in enumerate(conversation, 1):
            print(f"\nTurn {turn_idx}: {question}")
            print(f"Expected keywords: {keywords}")

            try:
                result = engine.chat(question, session_id=session_id)
                answer = result["response"]

                has_answer = answer and "không tìm thấy" not in answer.lower()

                if has_answer:
                    all_found, missing = check_keywords(answer, keywords)

                    if all_found:
                        print("✅ PASS")
                        results.append(("PASS", question))
                    else:
                        print(f"⚠️  PARTIAL - Missing: {missing}")
                        results.append(("PARTIAL", question))
                else:
                    print("❌ FAIL")
                    results.append(("FAIL", question))

            except Exception as e:
                print(f"❌ ERROR: {e}")
                results.append(("ERROR", question))

    # Summary
    print("\n" + "="*60)
    print("CHAT ENGINE SUMMARY")
    print("="*60)

    pass_count = sum(1 for r in results if r[0] == "PASS")
    partial_count = sum(1 for r in results if r[0] == "PARTIAL")
    fail_count = sum(1 for r in results if r[0] == "FAIL")

    total = len(results)
    accuracy = (pass_count / total * 100) if total > 0 else 0

    print(f"\nTotal turns: {total}")
    print(f"✅ Pass: {pass_count} ({pass_count/total*100:.1f}%)")
    print(f"⚠️  Partial: {partial_count} ({partial_count/total*100:.1f}%)")
    print(f"❌ Fail: {fail_count} ({fail_count/total*100:.1f}%)")
    print(f"\nAccuracy Score: {accuracy:.1f}%")

    return results


def main():
    """Run all accuracy tests."""
    print("\n" + "="*60)
    print("🧪 UIT AI AGENT - ACCURACY TESTING")
    print("="*60)
    print("\nThis tests the accuracy of retrieval and response quality.")
    print("Run this after tuning parameters to measure improvements.\n")

    # Test Query Engine
    query_results = test_query_engine()

    # Test Chat Engine
    chat_results = test_chat_engine()

    print("\n" + "="*60)
    print("🎉 ALL TESTS COMPLETED")
    print("="*60)
    print("\nTo improve accuracy, try:")
    print("1. Increase SIMILARITY_TOP_K in config/settings.py")
    print("2. Lower MINIMUM_SCORE_THRESHOLD")
    print("3. Add more training data to vector store")
    print("4. Tune prompts for better instruction following")


if __name__ == "__main__":
    main()
