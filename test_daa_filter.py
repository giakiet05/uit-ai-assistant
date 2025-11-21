"""Test DAA URL filter."""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from crawler.filters.daa_filter import DaaUrlFilter


def test_daa_filter():
    """Test filter với các URLs mẫu."""
    
    filter = DaaUrlFilter()
    
    test_cases = [
        # (URL, expected_important, description)
        ("https://daa.uit.edu.vn/thong-bao/2024/quy-dinh", True, "Thông báo 2024"),
        ("https://daa.uit.edu.vn/lich-thi/2025/ky-1", True, "Lịch thi 2025"),
        ("https://daa.uit.edu.vn/tot-nghiep/huong-dan", True, "Hướng dẫn tốt nghiệp"),
        ("https://daa.uit.edu.vn/node/12345", False, "Node URL"),
        ("https://daa.uit.edu.vn/thong-bao/2020/cu", False, "Năm cũ (2020)"),
        ("https://daa.uit.edu.vn/user/login", False, "User page"),
        ("https://daa.uit.edu.vn/search?q=test", False, "Search page"),
    ]
    
    print("=" * 60)
    print("TESTING DAA URL FILTER")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for url, expected, description in test_cases:
        result = filter.is_important(url)
        priority = filter.get_priority(url)
        
        status = "✅ PASS" if result == expected else "❌ FAIL"
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{status}: {description}")
        print(f"  URL: {url}")
        print(f"  Expected: {expected}, Got: {result}")
        print(f"  Priority: {priority}/100")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    import sys
    success = test_daa_filter()
    sys.exit(0 if success else 1)