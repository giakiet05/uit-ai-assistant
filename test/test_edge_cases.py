"""
Test edge cases for SmartNodeSplitter:
1. Mục với a) và a.
2. Header bị tách riêng (### 1. \n Nội dung...)
3. Bullet points bị đánh header (#### - Item)
4. Format khác (I > 1 > Bước 1)
"""

from pathlib import Path
from llama_index.core import Document
from src.knowledge_builder.indexing.splitters.smart_node_splitter import SmartNodeSplitter


def test_edge_cases():
    """Test various edge cases."""

    # ========== SETUP ==========

    test_file = Path(__file__).parent / "test_edge_cases.md"

    with open(test_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    doc = Document(
        text=markdown_content,
        metadata={
            "document_id": "test_edge_cases",
            "title": "Edge Cases Test",
            "category": "regulation"
        }
    )

    # ========== PARSE ==========

    print("\n" + "="*80)
    print("Testing Edge Cases (SmartNodeSplitter)")
    print("="*80 + "\n")

    splitter = SmartNodeSplitter(
        max_tokens=7000,
        enable_title_merging=False,  # Disable to see all chunks
        enable_pattern_detection=True
    )

    nodes = splitter.get_nodes_from_documents([doc])

    print(f"\n📊 Total nodes: {len(nodes)}\n")

    # ========== PRINT ALL CHUNKS ==========

    for i, node in enumerate(nodes):
        header_path = node.metadata.get('header_path', [])
        current_header = node.metadata.get('current_header', '')

        full_path = header_path.copy()
        if current_header:
            full_path.append(current_header)

        hierarchy = ' > '.join(full_path) if full_path else '(root)'

        print(f"📄 CHUNK #{i+1}")
        print("─"*80)
        print(f"Current Header: {current_header or '(none)'}")
        print(f"Hierarchy: {hierarchy}")
        print(f"Tokens: {node.metadata.get('token_count', 'N/A')}")
        print(f"\nContent (first 200 chars):")
        print(node.text[:200].replace('\n', ' '))
        print("\n" + "─"*80 + "\n")

    # ========== SUMMARY ==========

    print("\n" + "="*80)
    print("✅ Test Complete!")
    print("="*80)
    print("\nCheck the output above for:")
    print("1. ✅ Mục a) và Mục b. should both be detected")
    print("2. ✅ Bullet points (#### -) should be converted to (- )")
    print("3. ✅ All formats (CHƯƠNG/Điều and I/1/Bước) should work")


if __name__ == "__main__":
    test_edge_cases()
