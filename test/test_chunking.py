"""
Test Custom HierarchicalMarkdownParser.
Shows token counts, parent-child relationships, and hierarchy structure.
"""
from pathlib import Path
from llama_index.core import Document
from llama_index.core.schema import NodeRelationship
from src.indexing.hierarchical_markdown_parser import HierarchicalMarkdownParser


def test_chunking(file_path: str):
    """Test hierarchical markdown chunking cho 1 file markdown."""
    print(f"\n{'='*70}")
    print(f"Testing HierarchicalMarkdownParser for: {Path(file_path).name}")
    print(f"{'='*70}\n")

    # Read file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse to nodes with custom parser
    doc = Document(text=content)
    parser = HierarchicalMarkdownParser(
        max_tokens=7000,  # Conservative limit
        sub_chunk_size=1024,
        sub_chunk_overlap=128
    )
    nodes = parser.get_nodes_from_documents([doc])

    # Show stats
    stats = parser.get_stats()
    total_tokens = parser.count_tokens(content)

    print(f"📄 Original file:")
    print(f"   {len(content)} chars")
    print(f"   {len(content.split())} words")
    print(f"   {total_tokens} tokens")
    print()
    print(f"📊 Parsing Stats:")
    print(f"   Initial MD nodes: {stats['total_nodes']}")
    print(f"   Large nodes split: {stats['large_nodes_split']}")
    print(f"   Final nodes: {stats['final_nodes']}")
    print()

    print(f"📊 Total chunks: {len(nodes)}\n")
    print("="*70)

    # Separate nodes by hierarchy level
    leaf_nodes = []
    child_nodes = []

    for node in nodes:
        if NodeRelationship.PARENT in node.relationships:
            child_nodes.append(node)
        else:
            leaf_nodes.append(node)

    print(f"\n🌲 Hierarchy Structure:")
    print(f"   Leaf nodes (no parent): {len(leaf_nodes)}")
    print(f"   Child nodes (has parent): {len(child_nodes)}")
    print()

    # Print each node with hierarchy info
    for i, node in enumerate(nodes, 1):
        tokens = parser.count_tokens(node.text)
        is_child = NodeRelationship.PARENT in node.relationships

        # Determine node type
        if is_child:
            node_type = "👶 CHILD"
        else:
            node_type = "📄 LEAF"

        print(f"\n--- {node_type} CHUNK {i}/{len(nodes)} ---")
        print(f"Node ID: {node.node_id[:16]}...")
        print(f"Length: {len(node.text)} chars ({len(node.text.split())} words)")
        print(f"Tokens: {tokens} {'⚠️ EXCEEDS 8192!' if tokens > 8192 else '✅ OK'}")

        # Show parent relationship
        if is_child:
            parent_info = node.relationships[NodeRelationship.PARENT]
            print(f"🔗 Parent: {parent_info.node_id[:16]}...")

        # Show metadata if available
        if node.metadata:
            header = node.metadata.get("Header_1") or node.metadata.get("Header_2") or "No header"
            print(f"📑 Header: {header}")

        # Preview first 300 chars
        preview = node.text[:300].replace("\n", " ")
        print(f"Preview: {preview}...")

        # Check if contains table
        if "|" in node.text and "---|" in node.text:
            table_lines = [line for line in node.text.split("\n") if "|" in line]
            print(f"📊 Contains table: {len(table_lines)} rows")


if __name__ == "__main__":
    # Test file (thay đổi path nếu cần)
    test_file = "../data/processed/daa.uit.edu.vn/regulation/06-quyet-dinh-ve-viec-ban-hanh-quy-dinh-ve-khoa-luan-tot-nghiep-cho-sv-he-cq__159-qd-dhcntt_05-03-2024_ban_hanh_quy_dinh_kltn.md"
    if not Path(test_file).exists():
        print(f"[ERROR] File not found: {test_file}")
        print("\nTìm file khác để test:")
        curriculum_dir = Path("../data/processed/daa.uit.edu.vn/curriculum/")
        if curriculum_dir.exists():
            files = list(curriculum_dir.glob("content-*.md"))[:5]
            for f in files:
                print(f"  - {f}")
    else:
        test_chunking(test_file)
