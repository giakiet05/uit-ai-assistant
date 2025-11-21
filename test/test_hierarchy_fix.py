"""
Test hierarchy truncation to verify no duplication.

This test specifically checks that:
1. Hierarchy metadata is short and clean
2. No duplication between hierarchy and content
3. Long headers are truncated to "Khoản X", "Mục a", etc.
"""

from pathlib import Path
from llama_index.core import Document
from src.indexing.splitters.smart_node_splitter import SmartNodeSplitter


def test_hierarchy_truncation():
    """Test that hierarchy is truncated and not duplicated."""

    # ========== SETUP ==========

    # Use the fixer output from previous test
    fixer_output_path = Path(__file__).parent / "test_fixer_output.md"

    if not fixer_output_path.exists():
        print(f"❌ File not found: {fixer_output_path}")
        print("   Run test_fixer.py first to generate the file!")
        return

    with open(fixer_output_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    # Create document
    doc = Document(
        text=markdown_content,
        metadata={
            "document_id": "Test_Fixer_Output",
            "title": "Test Fixer Output (547)",
            "category": "regulation",
            "effective_date": "2024-01-01",
            "document_type": "original"
        }
    )

    # ========== PARSE WITH SMART SPLITTER ==========

    print("\n" + "="*80)
    print("Testing Hierarchy Truncation (SmartNodeSplitter)")
    print("="*80 + "\n")

    splitter = SmartNodeSplitter(
        max_tokens=7000,
        sub_chunk_size=1024,
        sub_chunk_overlap=200,
        enable_title_merging=True,
        enable_pattern_detection=True
    )

    nodes = splitter.get_nodes_from_documents([doc])

    # ========== FIND CHUNK #10 (or similar nested chunk) ==========

    print(f"\n📊 Total nodes: {len(nodes)}\n")

    # Find first chunk with nested hierarchy (3+ levels)
    for i, node in enumerate(nodes):
        # Build hierarchy from header_path + current_header
        header_path = node.metadata.get('header_path', [])
        current_header = node.metadata.get('current_header', '')

        full_path = header_path.copy()
        if current_header:
            full_path.append(current_header)

        hierarchy = ' > '.join(full_path)

        # Count levels (by counting ">")
        level_count = hierarchy.count('>')

        if level_count >= 2:  # At least 3 levels
            print(f"📄 CHUNK #{i+1} (Nested Hierarchy Example)")
            print("─"*80)
            print(f"Header: {node.metadata.get('current_header', 'N/A')}")
            print(f"Level: {node.metadata.get('level', 'N/A')}")
            print(f"Hierarchy: {hierarchy}")
            print(f"Tokens: {node.metadata.get('token_count', 'N/A')}")
            print(f"\n{'▼'*40} FULL CONTENT {'▼'*40}")
            print(node.text[:1000])  # First 1000 chars
            print(f"{'▲'*40} END CONTENT {'▲'*40}\n")

            # ========== CHECK FOR DUPLICATION ==========

            hierarchy_parts = hierarchy.split(' > ')
            content_text = node.text

            print("\n🔍 CHECKING FOR DUPLICATION:\n")

            # Check if last hierarchy part is duplicated in content
            if hierarchy_parts:
                last_part = hierarchy_parts[-1]
                print(f"  Last hierarchy part: {last_part}")

                if len(last_part) > 80:
                    print(f"  ❌ WARNING: Last part is too long ({len(last_part)} chars)")
                    print(f"     This might cause duplication!")
                else:
                    print(f"  ✅ Last part is short ({len(last_part)} chars)")

                # Count occurrences in full content
                count = content_text.count(last_part)
                print(f"  Occurrences in content: {count}")

                if count > 2:
                    print(f"  ⚠️  Possible duplication detected!")
                elif count == 1:
                    print(f"  ✅ No duplication!")

            print("\n" + "─"*80 + "\n")

            # Only show first 3 examples
            if i >= 10:
                break

    # ========== SUMMARY ==========

    print("\n" + "="*80)
    print("✅ Test Complete!")
    print("="*80)
    print("\nCheck the output above for:")
    print("1. Hierarchy should be SHORT (e.g., 'CHƯƠNG I > Điều 1 > Khoản 1')")
    print("2. No long content in hierarchy metadata")
    print("3. Content should NOT be duplicated in hierarchy")


if __name__ == "__main__":
    test_hierarchy_truncation()
