"""
Quick test for QueryRefiner.
"""

from src.engines.query_refinement import QueryRefiner


def test_query_refiner():
    """Test query refinement functionality."""

    refiner = QueryRefiner()

    print("="*60)
    print("TESTING QUERY REFINER")
    print("="*60)

    # Test 1: Known acronyms - should expand
    print("\n[Test 1] Known acronyms")
    query1 = "điều kiện TN của UIT ngành CNTT"
    result1 = refiner.refine(query1)
    print(f"Input:  {query1}")
    print(f"Output: {result1}")
    assert result1 is not None
    assert "Tốt nghiệp" in result1
    assert "Trường Đại học" in result1
    assert "Công nghệ Thông tin" in result1
    print("✅ PASS")

    # Test 2: Unknown acronym - should return None
    print("\n[Test 2] Unknown acronym")
    query2 = "ABCXYZ là gì?"
    result2 = refiner.refine(query2)
    print(f"Input:  {query2}")
    print(f"Output: {result2}")
    assert result2 is None

    unknown2 = refiner.get_unknown_acronyms(query2)
    print(f"Unknown: {unknown2}")
    assert "ABCXYZ" in unknown2
    print("✅ PASS")

    # Test 3: No acronyms - should return original
    print("\n[Test 3] No acronyms")
    query3 = "điều kiện tốt nghiệp là gì?"
    result3 = refiner.refine(query3)
    print(f"Input:  {query3}")
    print(f"Output: {result3}")
    assert result3 == query3
    print("✅ PASS")

    # Test 4: Informal language - should preserve
    print("\n[Test 4] Informal language preserved")
    query4 = "tao bị fail môn, UIT có cho thi lại không?"
    result4 = refiner.refine(query4)
    print(f"Input:  {query4}")
    print(f"Output: {result4}")
    assert result4 is not None
    assert "tao" in result4  # Informal word preserved
    assert "fail" in result4  # Slang preserved
    assert "Trường Đại học" in result4  # Acronym expanded
    print("✅ PASS")

    # Test 5: Multiple same acronyms
    print("\n[Test 5] Multiple occurrences of same acronym")
    query5 = "UIT và ĐHQG có khác nhau không? UIT thuộc ĐHQG phải không?"
    result5 = refiner.refine(query5)
    print(f"Input:  {query5}")
    print(f"Output: {result5}")
    assert result5 is not None
    assert result5.count("Trường Đại học Công nghệ Thông tin") == 2
    print("✅ PASS")

    # Test 6: Case insensitive - lowercase acronyms
    print("\n[Test 6] Case insensitive - lowercase")
    query6 = "uit có mấy ngành? cntt học những gì?"
    result6 = refiner.refine(query6)
    print(f"Input:  {query6}")
    print(f"Output: {result6}")
    assert result6 is not None
    assert "Trường Đại học" in result6
    assert "Công nghệ Thông tin" in result6
    print("✅ PASS")

    # Test 7: Mixed case
    print("\n[Test 7] Mixed case")
    query7 = "Uit và cntt"
    result7 = refiner.refine(query7)
    print(f"Input:  {query7}")
    print(f"Output: {result7}")
    assert result7 is not None
    print("✅ PASS")

    print("\n" + "="*60)
    print("ALL TESTS PASSED ✅")
    print("="*60)


if __name__ == "__main__":
    test_query_refiner()
