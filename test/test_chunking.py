"""
Test Custom HierarchicalMarkdownParserV2.
Shows token counts, hierarchy structure, and context prepending.
"""
from pathlib import Path
from llama_index.core import Document
from src.indexing.hierarchical_markdown_parser_v2 import HierarchicalMarkdownParserV2
import json


def test_chunking(file_path: str, metadata_path: str = None):
    """Test hierarchical markdown chunking cho 1 file markdown với metadata."""
    print(f"\n{'='*70}")
    print(f"Testing HierarchicalMarkdownParserV2 for: {Path(file_path).name}")
    print(f"{'='*70}\n")

    # Read file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Load metadata if exists
    metadata = {}
    if metadata_path and Path(metadata_path).exists():
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        print(f"✅ Loaded metadata from: {Path(metadata_path).name}")
    else:
        # Try to auto-find metadata file
        auto_metadata_path = Path(file_path).with_suffix('.json')
        if auto_metadata_path.exists():
            with open(auto_metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            print(f"✅ Auto-loaded metadata from: {auto_metadata_path.name}")
        else:
            print("⚠️  No metadata file found, using minimal metadata")
            metadata = {
                "document_id": Path(file_path).stem,
                "category": "unknown"
            }

    print(f"📋 Metadata: {json.dumps(metadata, ensure_ascii=False, indent=2)}\n")

    # Parse to nodes with custom parser V2
    doc = Document(text=content, metadata=metadata)
    parser = HierarchicalMarkdownParserV2(
        max_tokens=7000,
        sub_chunk_size=1024,
        sub_chunk_overlap=200
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
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Large chunks split: {stats['large_chunks_split']}")
    print(f"   Final nodes: {stats['final_nodes']}")
    print()

    print(f"📊 Total chunks: {len(nodes)}\n")
    print("="*70)

    # Print each node with hierarchy info
    for i, node in enumerate(nodes, 1):
        tokens = parser.count_tokens(node.text)

        # Check if sub-chunked
        is_sub_chunked = node.metadata.get('is_sub_chunked', False)
        node_type = "🔪 SUB-CHUNK" if is_sub_chunked else "📄 CHUNK"

        print(f"\n--- {node_type} {i}/{len(nodes)} ---")
        print(f"Node ID: {node.node_id[:16]}...")
        print(f"Length: {len(node.text)} chars ({len(node.text.split())} words)")
        print(f"Tokens: {tokens} {'⚠️ EXCEEDS 8192!' if tokens > 8192 else '✅ OK'}")

        # Show hierarchy metadata (NEW IN V2!)
        header_path = node.metadata.get('header_path', [])
        current_header = node.metadata.get('current_header')
        header_level = node.metadata.get('header_level', 0)

        if header_path or current_header:
            print(f"\n🗂️  Hierarchy Info:")
            print(f"   Header path (parents): {header_path}")
            print(f"   Current header: {current_header}")
            print(f"   Level: {header_level}")

            # Show display format (like in retrieval)
            full_path = header_path.copy()
            if current_header:
                full_path.append(current_header)
            if full_path:
                display = " > ".join(full_path)
                print(f"   Display: {display}")

        # Show sub-chunk info
        if is_sub_chunked:
            sub_idx = node.metadata.get('sub_chunk_index', 0)
            total_subs = node.metadata.get('total_sub_chunks', 0)
            parent_tokens = node.metadata.get('parent_chunk_tokens', 0)
            print(f"\n🔪 Sub-chunk: {sub_idx + 1}/{total_subs} (parent had {parent_tokens} tokens)")

        # Preview first 400 chars
        preview = node.text[:400].replace("\n", " ")
        print(f"\n📝 Preview: {preview}...")

        # Check if contains table
        if "|" in node.text and "---|" in node.text:
            table_lines = [line for line in node.text.split("\n") if "|" in line]
            print(f"📊 Contains table: {len(table_lines)} rows")


if __name__ == "__main__":
    import sys

    # Test file (pass as argument or use default)
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    else:
       test_file = "data/processed/regulation/790-qd-dhcntt_28-9-22_quy_che_dao_tao.md"

    # Check if file exists
    if not Path(test_file).exists():
        print(f"[ERROR] File not found: {test_file}\n")
        print("Tìm file khác để test:")

        # Try to find sample files in processed directories
        for category in ["regulation", "curriculum"]:
            cat_dir = Path(f"data/processed/{category}")
            if cat_dir.exists():
                files = list(cat_dir.glob("*.md"))[:3]
                if files:
                    print(f"\n📁 {category}:")
                    for f in files:
                        print(f"  - {f}")

        print("\nUsage:")
        print("  python test/test_chunking.py <file_path>")
        print("  python test/test_chunking.py data/processed/regulation/some-file.md")
    else:
        test_chunking(test_file)
